# data_processor/master_connector.py

from typing import List, Dict, Any
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from .constants import WORKER_ADDRESSES

WORKER_REBUILD_PATH = "/rebuild"
TIMEOUT_SECONDS = 300  # 5분 타임아웃


def call_worker_rebuild(worker_info: Dict[str, Any]) -> Dict[str, Any]:
    """단일 워커에게 Importer 재생성 명령을 HTTP로 전송하고 결과를 반환합니다."""

    worker_host = worker_info['host']
    worker_port = worker_info['port']
    worker_name = worker_info['name']

    url = f"http://{worker_host}:{worker_port}{WORKER_REBUILD_PATH}"

    start_time = time.time()
    response_data: Dict[str, Any] = {
        "worker": worker_name,
        "status": "INITIATED",
        "message": f"URL: {url}",
        "processing_time": 0.0,
        "communication_time": 0.0,
        "records_inserted": 0,
    }

    print(f"📤 {worker_name}: {url}로 명령 전송 시작...")

    try:
        # 워커 서버에 POST 요청
        # 워커 서버의 `/rebuild/` 엔드포인트는 해당 워커의 importer.py 로직을 실행하도록 구현되어야 합니다.
        response = requests.post(url, timeout=TIMEOUT_SECONDS)
        comm_end_time = time.time()

        response_data["communication_time"] = comm_end_time - start_time

        if response.status_code == 200 or response.status_code == 202:
            # 워커가 보낸 JSON 본문을 파싱
            worker_response = response.json()

            # 202인 경우 상태를 'ACCEPTED'로 설정
            if response.status_code == 202:
                response_data["status"] = "ACCEPTED"
            else:
                response_data["status"] = worker_response.get("status", "SUCCESS")

            response_data["message"] = worker_response.get("message", "워커 처리 성공")
            response_data["processing_time"] = worker_response.get("processing_time", 0.0)
            response_data["records_inserted"] = worker_response.get("records_inserted", 0)

        elif response.status_code == 400:
            response_data["status"] = "CLIENT_ERROR"
            response_data["message"] = f"워커 요청 오류: {response.text}"
        elif response.status_code == 403:
            response_data["status"] = "REFUSED"
            response_data["message"] = "워커 연결 거부 (CORS/인증 오류)"
        else:
            response_data["status"] = "HTTP_ERROR"
            response_data["message"] = f"워커 HTTP 오류: Status {response.status_code}, {response.text}"

    except requests.exceptions.Timeout:
        response_data["status"] = "TIMEOUT"
        response_data["message"] = f"워커 응답 시간 초과 ({TIMEOUT_SECONDS}초)"
    except requests.exceptions.ConnectionError:
        response_data["status"] = "CONNECTION_ERROR"
        response_data["message"] = f"워커 연결 오류 (URL: {url} 확인 필요)"
    except Exception as e:
        response_data["status"] = "UNKNOWN_ERROR"
        response_data["message"] = f"알 수 없는 오류: {e}"

    print(f"📥 {worker_name}: {response_data['status']} 수신. (Comm Time: {response_data['communication_time']:.4f}초)")
    return response_data


def distribute_importer_rebuild() -> Dict[str, Any]:
    """
    모든 워커들에게 병렬로 데이터 재생성 명령을 전송하고 결과를 종합합니다.
    """
    start_master_time = time.time()
    results: List[Dict[str, Any]] = []

    # ThreadPoolExecutor를 사용하여 워커에게 비동기 병렬 요청
    with ThreadPoolExecutor(max_workers=len(WORKER_ADDRESSES)) as executor:
        future_to_worker = {
            executor.submit(call_worker_rebuild, worker_info): worker_info['name']
            for worker_info in WORKER_ADDRESSES
        }

        for future in as_completed(future_to_worker):
            worker_name = future_to_worker[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "worker": worker_name,
                    "status": "THREAD_ERROR",
                    "message": f"스레드 실행 중 치명적 오류: {e}",
                    "processing_time": 0.0,
                    "communication_time": 0.0,
                    "records_inserted": 0,
                })

    end_master_time = time.time()
    master_total_time = end_master_time - start_master_time

    return {
        "master_total_time": master_total_time,
        "results": results
    }