# data_processor/db_connector.py

from pymongo import MongoClient
from .constants import MONGO_URI, WORKER_NAME
import sys

# 전역 클라이언트 변수 (연결 재사용을 위해)
_mongo_client = None


def get_mongodb_client():
    """MongoDB 클라이언트 인스턴스를 반환합니다."""
    global _mongo_client

    if _mongo_client is not None:
        return _mongo_client

    # ✅ 디버깅을 위한 현재 접속 URI 출력
    print(f"[{WORKER_NAME}] MongoDB 연결 시도 URI: {MONGO_URI}", file=sys.stderr)

    try:
        # 클라이언트 연결 시도
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # 연결 확인 (실제 쿼리를 보내지 않고 연결 상태만 확인)
        _mongo_client.admin.command('ping')
        print(f"[{WORKER_NAME}] MongoDB 연결 성공.")
        return _mongo_client
    except Exception as e:
        # ✅ 구체적인 오류 메시지 출력
        print(f"[{WORKER_NAME}] ❌ MongoDB 연결 오류 발생: {e}", file=sys.stderr)
        _mongo_client = None
        return None


def close_mongodb_client():
    """MongoDB 연결을 종료합니다."""
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        print(f"[{WORKER_NAME}] MongoDB 연결 해제.")