# data_processor/cache_manager.py

from typing import List, Dict, Optional, Any
from collections import Counter
from .db_connector import get_mongodb_client
# 분산 처리 함수 임포트
from .master_connector import distribute_importer_rebuild
from .constants import (
    DB_NAME, RECORD_NOUNS_COLLECTION, TOP_NOUNS_CACHE_COLLECTION, TOP_N,
    DB_FIELD_HEADING, DB_FIELD_DATE, DB_FIELD_TAGS, DB_FIELD_NOUNS,
    CACHE_FIELD_TITLE_QUERY, CACHE_FIELD_START_DATE_QUERY, CACHE_FIELD_END_DATE_QUERY,
    CACHE_FIELD_TAGS_QUERY, CACHE_FIELD_TOP_N, CACHE_FIELD_TOP_WORDS
)


def get_top_nouns_from_cache(query_conditions: Dict[str, Any], top_n: int = TOP_N) -> Optional[
    List[Dict[str, Any]]]:
    """
    주어진 조건 딕셔너리와 top_n에 해당하는 결과를 캐시 컬렉션에서 조회합니다.
    """
    client = get_mongodb_client()
    if not client: return None
    db = client[DB_NAME]
    cache_collection = db[TOP_NOUNS_CACHE_COLLECTION]

    title = query_conditions.get('title', "")
    tags = query_conditions.get('tags', None)
    start_date = query_conditions.get('start_date', "")
    end_date = query_conditions.get('end_date', "")

    # 캐시 키를 위한 정규화된 태그 문자열 생성
    tags_key = ",".join(tags) if tags else ""

    query = {
        CACHE_FIELD_TITLE_QUERY: title,
        CACHE_FIELD_TAGS_QUERY: tags_key,
        CACHE_FIELD_START_DATE_QUERY: start_date,
        CACHE_FIELD_END_DATE_QUERY: end_date,
        CACHE_FIELD_TOP_N: top_n
    }
    cached_doc = cache_collection.find_one(query)
    client.close()

    if cached_doc:
        print(f"✅ 캐시에서 데이터를 찾았습니다.")
        return cached_doc.get(CACHE_FIELD_TOP_WORDS)

    print("❌ 캐시에 데이터가 없습니다. 새로 생성합니다.")
    return None


def calculate_and_save_top_nouns(query_conditions: Dict[str, Any], top_n: int = TOP_N) -> Optional[
    List[Dict[str, Any]]]:
    """
    'file_noun_records'에서 조건을 만족하는 레코드를 검색하고,
    명사 빈도수를 계산하여 상위 N개를 캐시에 저장합니다.
    (검색 결과가 없으면 워커에 재처리 명령을 내리고 한 번 더 시도합니다.)
    """
    client = get_mongodb_client()
    if not client: return None

    db = client[DB_NAME]
    record_collection = db[RECORD_NOUNS_COLLECTION]
    cache_collection = db[TOP_NOUNS_CACHE_COLLECTION]

    title = query_conditions.get('title', "")
    tags = query_conditions.get('tags', None)
    start_date = query_conditions.get('start_date', "")
    end_date = query_conditions.get('end_date', "")

    # 1. 'file_noun_records' 컬렉션에서 조건에 맞는 문서 검색을 위한 쿼리 설정
    query: Dict[str, Any] = {}

    # Title (Heading) 검색: 부분 일치 및 대소문자 무시 (i)
    if title: query[DB_FIELD_HEADING] = {"$regex": title, "$options": "i"}

    # Tags 검색: 주어진 태그 리스트 중 하나라도 포함하는 문서 ($in)
    if tags: query[DB_FIELD_TAGS] = {"$in": tags}

    # Date Range 검색
    date_query = {}
    if start_date: date_query["$gte"] = start_date
    if end_date: date_query["$lte"] = end_date
    if date_query: query[DB_FIELD_DATE] = date_query

    def fetch_records(collection) -> List[Dict[str, Any]]:
        """DB에서 레코드를 가져오는 내부 함수"""
        print(f"🔍 '{RECORD_NOUNS_COLLECTION}'에서 조건 ({query})에 맞는 레코드 검색 중...")
        # 필요한 필드(명사 리스트)만 가져와 네트워크 부하 줄이기
        return list(collection.find(query, {DB_FIELD_NOUNS: 1, "_id": 0}))

    # 1차 검색
    matching_records = fetch_records(record_collection)

    # --- [사용자 요청 로직: 검색 실패 시 워커 재처리 후 재시도] ---
    if not matching_records:
        print(f"⚠️ 경고: 1차 검색에서 조건 ({query})에 맞는 레코드가 없습니다. (검색 조건 미일치)")
        print("🚀 워커들에게 분산 Importer 재처리 명령을 요청하고 재시도합니다...")

        try:
            # 1. 워커에게 재처리 명령 요청
            rebuild_result = distribute_importer_rebuild()
            print("✅ 워커 재처리 명령 완료. 2차 검색을 시도합니다.")

            # 2. 2차 검색 시도
            matching_records = fetch_records(record_collection)  # 2차 검색

        except Exception as e:
            print(f"❌ 워커 재처리 명령 중 치명적인 오류 발생: {e}")

    if not matching_records:
        client.close()
        print(f"⚠️ 경고: 최종적으로 조건 ({query})에 맞는 레코드가 '{RECORD_NOUNS_COLLECTION}'에 없습니다. (검색 조건 미일치)")
        return []

    # 2. 명사 종합 및 빈도수 계산
    all_nouns = []
    for record in matching_records:
        all_nouns.extend(record.get(DB_FIELD_NOUNS, []))

    noun_counts = Counter(all_nouns)
    top_n_words = noun_counts.most_common(top_n)

    top_words_for_db = [{"word": word, "count": count} for word, count in top_n_words]

    # 3. 새로운 MongoDB 컬렉션에 저장 (캐시)
    tags_key = ",".join(tags) if tags else ""
    cache_document = {
        CACHE_FIELD_TITLE_QUERY: title,
        CACHE_FIELD_TAGS_QUERY: tags_key,
        CACHE_FIELD_START_DATE_QUERY: start_date,
        CACHE_FIELD_END_DATE_QUERY: end_date,
        CACHE_FIELD_TOP_N: top_n,
        "total_records": len(matching_records),
        CACHE_FIELD_TOP_WORDS: top_words_for_db
    }
    # 캐시 문서를 유일하게 식별할 수 있는 쿼리
    cache_query = {k: cache_document[k] for k in
                   [CACHE_FIELD_TITLE_QUERY, CACHE_FIELD_TAGS_QUERY, CACHE_FIELD_START_DATE_QUERY,
                    CACHE_FIELD_END_DATE_QUERY, CACHE_FIELD_TOP_N]}

    # Upsert를 사용하여 캐시 존재 시 업데이트, 없으면 삽입
    cache_collection.replace_one(cache_query, cache_document, upsert=True)
    client.close()

    return top_words_for_db


def get_top_nouns_for_conditions(query_conditions: Dict[str, Any], top_n: int = TOP_N) -> Optional[
    List[Dict[str, Any]]]:
    """
    메인 진입 함수: 캐시 확인 후, 없으면 계산 및 저장 후 결과를 반환합니다.
    (calculate_and_save_top_nouns 내부에서 조건 검색 실패 시 분산 재처리가 자동으로 수행됩니다.)
    """
    title = query_conditions.get('title')
    tags = query_conditions.get('tags')
    start_date = query_conditions.get('start_date')
    end_date = query_conditions.get('end_date')

    if not (title or tags or start_date or end_date):
        print("❌ 오류: Title, Tags, Start Date/End Date 중 최소한 하나는 입력되어야 합니다.")
        return None

    tt = title if title is not None else ""
    tg = tags if tags is not None else None
    sd = start_date if start_date is not None else ""
    ed = end_date if end_date is not None else ""

    processed_conditions = {
        'title': tt, 'tags': tg, 'start_date': sd, 'end_date': ed,
    }

    # 1. 캐시 확인
    cached_result = get_top_nouns_from_cache(processed_conditions, top_n)
    if cached_result is not None:
        return cached_result

    # 2. 중간 데이터 DB에서 계산 및 저장
    print("⚠️ 캐시 미스. 중간 데이터 DB에서 명사 집계 및 캐시 저장 시작...")

    # calculate_and_save_top_nouns 내부에서 1차 검색 실패 시 자동 재처리 및 2차 검색이 실행됩니다.
    result = calculate_and_save_top_nouns(processed_conditions, top_n)

    return result