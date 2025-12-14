# data_processor/importer.py 또는 data_processor/db_utils.py 파일에 추가

from .db_connector import get_mongodb_client
from .constants import DB_NAME, RECORD_NOUNS_COLLECTION, TOP_NOUNS_CACHE_COLLECTION
import sys


# ... (기존 extract_and_filter_proper_nouns, parse_tags, process_worker_files 함수 유지) ...

# 🌟 새로운 DB 초기화 함수 🌟
def reset_all_db():
    client = get_mongodb_client()
    if client is None:
        print("❌ MongoDB 클라이언트에 연결할 수 없어 DB 초기화를 건너뜁니다.", file=sys.stderr)
        return False

    try:
        db = client[DB_NAME]  # 데이터베이스 객체를 가져옴

        # 1. 특정 컬렉션만 Drop
        collections_to_drop = [RECORD_NOUNS_COLLECTION, TOP_NOUNS_CACHE_COLLECTION]

        for collection_name in collections_to_drop:
            if collection_name in db.list_collection_names():
                db[collection_name].drop()
                print(f"✅ 컬렉션 '{collection_name}'을 성공적으로 삭제했습니다.")
            else:
                # 이미 삭제되었거나 존재하지 않는 경우
                pass

        print(f"✅ 데이터베이스 '{DB_NAME}' 내의 주요 분석 컬렉션을 성공적으로 초기화했습니다.")
        return True

    except Exception as e:
        print(f"❌ DB 초기화 중 치명적인 오류 발생: {e}", file=sys.stderr)
        raise Exception(f"MongoDB Drop 실패: {e}")
    finally:
        pass