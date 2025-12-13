# data_processor/db_connector.py

from pymongo import MongoClient
from .constants import MONGO_URI, WORKER_NAME
import sys

# 전역 클라이언트 변수: (주의: 워커의 Importer 작업은 사용하지 않고, Django/Master 서버의 다른 용도로만 유지)
_mongo_client = None


def get_mongodb_client():
    """
    MongoDB 클라이언트 인스턴스를 반환합니다.
    워커의 백그라운드 스레드에서 호출 시, 항상 새로운 독립적인 연결을 생성합니다.
    """
    try:
        # 🌟 새로운 독립적인 클라이언트 연결 생성 (글로벌 캐시 사용 안함) 🌟
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # 연결 확인
        client.admin.command('ping')
        print(f"[{WORKER_NAME}] MongoDB 독립 연결 생성 성공.")
        return client
    except Exception as e:
        print(f"[{WORKER_NAME}] ❌ MongoDB 연결 오류 발생: {e}", file=sys.stderr)
        return None


def close_mongodb_client():
    """
    전역 MongoDB 연결 (_mongo_client)을 종료합니다.
    (워커의 Importer 작업은 독립 연결을 사용하므로, 이 함수는 주로 다른 용도로 사용됩니다.)
    """
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        print(f"[{WORKER_NAME}] 전역 MongoDB 연결 해제.")