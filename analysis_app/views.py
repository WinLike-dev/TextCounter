# analysis_app/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from wordcloud import WordCloud
import io
import base64
from typing import List, Tuple, Optional, Dict, Any
# 마스터 로직 임포트
from data_processor.cache_manager import get_top_nouns_for_conditions
from data_processor.importer import reset_all_db  # 마스터 전용 DB 초기화 함수 사용
from data_processor.master_connector import distribute_importer_rebuild  # 분산 처리 기능 사용
from data_processor.constants import TOP_N
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json


def generate_word_cloud_image(word_counts: List[Dict[str, int]]) -> Optional[str]:
    """WordCloud 이미지를 생성하고 base64 문자열로 반환합니다. (dict 형식에 맞게 수정)"""
    word_freq_dict = {item['word']: item['count'] for item in word_counts}
    if not word_freq_dict: return None

    try:
        # 폰트 경로 필요시 수정
        font_path = 'static/malgun.ttf'
        wc = WordCloud(
            background_color="white",
            width=800, height=400, max_words=len(word_freq_dict),
            font_path=font_path
        )
    except ValueError:
        # 폰트가 없을 경우 기본 폰트 사용
        wc = WordCloud(
            background_color="white",
            width=800, height=400, max_words=len(word_freq_dict)
        )

    wc.generate_from_frequencies(word_freq_dict)

    img_io = io.BytesIO()
    wc.to_image().save(img_io, format='PNG')
    img_io.seek(0)

    return 'data:image/png;base64,' + base64.b64encode(img_io.read()).decode()


def index(request):
    """메인 페이지 뷰 (분산 전용)"""
    success_message = request.session.pop('success_message', None)
    warning_message = request.session.pop('warning_message', None)

    # 중간 데이터 존재 여부 확인 로직 제거로 이 플래그는 항상 False
    show_rebuild_prompt = False

    query_params = {
        'title': request.GET.get('title', ''),
        'tags': request.GET.get('tags', ''),
        'start_date': request.GET.get('start_date', ''),
        'end_date': request.GET.get('end_date', ''),
        'top_n': request.GET.get('top_n', str(TOP_N)),
    }

    return render(request, 'analysis_app/index.html', {
        'success_message': success_message,
        'warning_message': warning_message,
        'TOP_N': TOP_N,
        'show_rebuild_prompt': show_rebuild_prompt,
        'query_params': query_params,
    })

@csrf_exempt
def start_distributed_rebuild_view(request):
    """[분산 병렬] DB 데이터 재생성 AJAX 요청 처리 뷰 (워커 호출)"""
    if request.method == 'POST':
        request.session.modified = False
        try:
            # master_connector.py의 로직 호출
            response_data = distribute_importer_rebuild()

            master_total_time = response_data.get('master_total_time', 0.0)

            request.session['success_message'] = f"✅ 분산 병렬 ImFiles 데이터 재생성 완료! (마스터 총 경과 시간: {master_total_time:.4f}초)"

            return JsonResponse({
                "status": "COMPLETED",
                "message": "분산 명령 및 응답 수신 완료",
                "data": response_data
            })
        except Exception as e:
            return JsonResponse({
                "status": "MASTER_ERROR",
                "message": f"마스터 처리 중 오류 발생: {e}"
            }, status=500)

    return JsonResponse({"status": "ERROR", "message": "잘못된 요청 방식"}, status=400)


def reset_all_db_view(request):
    """모든 DB 컬렉션을 비우는 뷰 (importer.py의 reset_all_db 호출)"""
    if request.method == 'POST':
        try:
            if reset_all_db():
                request.session['success_message'] = "🗑️ 모든 DB 컬렉션이 성공적으로 초기화되었습니다."
            else:
                request.session['success_message'] = "⚠️ DB 초기화 중 오류가 발생했습니다. 로그를 확인하세요."
        except Exception as e:
            return render(request, 'analysis_app/error.html', {
                'message': f'DB 초기화 중 치명적인 오류 발생: {e}'
            }, status=500)

    return redirect(reverse('index'))


def wordcloud_view(request):
    """
    WordCloud 표시 뷰: GET 쿼리 매개변수를 받아 조건부 워드클라우드를 생성합니다.
    """

    # 1. 쿼리 매개변수 추출
    title = request.GET.get('title')
    tags_input = request.GET.get('tags')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    top_n = request.GET.get('top_n', TOP_N)

    try:
        top_n = int(top_n)
    except ValueError:
        top_n = TOP_N

    parsed_tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else None

    # 2. 쿼리 객체(딕셔너리) 구성
    query_conditions: Dict[str, Any] = {
        'title': title,
        'tags': parsed_tags,
        'start_date': start_date,
        'end_date': end_date,
    }

    # 유효성 검사: 최소 하나의 조건이 있어야 함
    if not (title or parsed_tags or start_date or end_date):
        return render(request, 'analysis_app/error.html', {
            'message': 'Title, Tags, Start Date, End Date 중 최소한 하나는 입력해야 합니다.'
        }, status=400)

    # 3. cache_manager를 통해 조건부 명사 데이터 가져오기
    # 이 함수 내부에서 1차 검색 실패 시 자동 재처리(rebuild) 후 2차 검색이 시도됩니다.
    top_words_data = get_top_nouns_for_conditions(
        query_conditions=query_conditions,
        top_n=top_n
    )

    if top_words_data is None:
        return render(request, 'analysis_app/error.html', {
            'message': '데이터를 처리하는 중 오류가 발생했습니다. 데이터베이스 연결을 확인하세요.'
        }, status=500)

    # 4. 데이터로 워드클라우드 이미지 생성
    image_base64 = generate_word_cloud_image(top_words_data)

    # 5. Context 구성 및 렌더링
    context = {
        'title': title or '전체',
        'tags': ', '.join(parsed_tags) if parsed_tags else '전체',
        'start_date': start_date or '전체',
        'end_date': end_date or '전체',
        'top_n': top_n,

        'image_base64': image_base64,
        'top_words': top_words_data,
    }

    return render(request, 'analysis_app/wordcloud.html', context)


@require_POST
@csrf_exempt
def worker_notification_view(request):
    """
    Worker 서버로부터 데이터 재생성 완료 상태를 JSON 형태로 수신합니다.
    (CSRF 토큰 검증은 비활성화합니다. 외부 API 통신이므로)
    """
    try:
        # 1. POST 본문에서 JSON 데이터 파싱
        data = json.loads(request.body.decode('utf-8'))

        worker_name = data.get('worker_name', 'UNKNOWN_WORKER')
        status = data.get('status', 'FAILURE')
        message = data.get('message', 'No message provided.')

        # 2. 콘솔에 로그 출력 (Master가 Worker의 완료 상태를 인지했음을 확인)
        # 이 로그가 Master 서버의 Docker 컨테이너 로그에 떠야 합니다.
        print(f"\n[Master] 🔔 Worker 알림 수신 ({worker_name})")
        print(f"[Master]   - 상태: {status}")
        print(f"[Master]   - 메시지: {message}")

        # 3. Master 로직 (예: 작업 완료 카운트 업데이트, 다음 작업 지시 등)
        # TODO: 필요하다면 여기에 분산 작업 상태를 관리하는 로직을 추가합니다.

        # 4. Worker에게 성공 응답 반환
        return JsonResponse({
            "status": "received",
            "message": f"Notification received from {worker_name}"
        }, status=200)

    except json.JSONDecodeError:
        print("[Master] ❌ Worker 알림 수신 오류: 유효하지 않은 JSON 형식")
        return JsonResponse({"status": "error", "message": "Invalid JSON format"}, status=400)

    except Exception as e:
        print(f"[Master] ❌ Worker 알림 처리 중 알 수 없는 오류: {e}")
        return JsonResponse({"status": "error", "message": f"Server error: {e}"}, status=500)