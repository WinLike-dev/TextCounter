# data_processor/importer.py 또는 data_processor/db_utils.py 파일에 추가

from .db_connector import get_mongodb_client
from .constants import DB_NAME
import sys


# ... (기존 extract_and_filter_proper_nouns, parse_tags, process_worker_files 함수 유지) ...

# 🌟 새로운 DB 초기화 함수 🌟
def reset_all_db():
    """
    Pymongo를 사용하여 데이터베이스를 직접 Drop합니다.
    (Djongo의 불안정한 DB 초기화 명령 회피)
    """
    client = get_mongodb_client()
    if client is None:
        print("❌ MongoDB 클라이언트에 연결할 수 없어 DB 초기화를 건너뜁니다.", file=sys.stderr)
        return False

    try:
        # 1. MongoDB 클라이언트를 통해 데이터베이스 객체를 가져옵니다.
        # DB가 존재하지 않아도 drop_database는 오류를 발생시키지 않습니다.
        client.drop_database(DB_NAME)
        print(f"✅ 데이터베이스 '{DB_NAME}'을 성공적으로 초기화(Drop)했습니다.")

        # 2. Django의 세션/Auth 테이블을 위해 강제로 마이그레이션을 다시 실행해야 할 수 있습니다.
        #    (여기서는 Pymongo만 사용하므로 필요 없음. Django ORM 호출 시에만 필요)
        return True

    except Exception as e:
        print(f"❌ DB 초기화 중 치명적인 오류 발생: {e}", file=sys.stderr)
        # 이 예외를 다시 발생시켜 Django ORM/View에서 오류를 잡을 수 있게 함
        raise Exception(f"MongoDB Drop 실패: {e}")
    finally:
        # DB 연결 재사용을 위해 client.close()는 하지 않습니다.
        pass