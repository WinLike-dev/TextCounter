# data_processor/db_connector.py

from pymongo import MongoClient
from .constants import MONGO_URI

def get_mongodb_client():
    """MongoDB 연결 객체를 반환합니다."""
    try:
        client = MongoClient(MONGO_URI)
        client.admin.command('ping')
        return client
    except Exception as e:
        print(f"ERROR: MongoDB 연결 실패. URI 및 인증 정보를 확인하세요: {e}")
        return None