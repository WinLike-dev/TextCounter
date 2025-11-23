# data_processor/cache_manager.py

from typing import List, Dict, Optional, Any
from collections import Counter
from .db_connector import get_mongodb_client
from .constants import (
    DB_NAME, RECORD_NOUNS_COLLECTION, TOP_NOUNS_CACHE_COLLECTION, TOP_N,
    # DB Document Fields
    DB_FIELD_HEADING, DB_FIELD_DATE, DB_FIELD_TAGS, DB_FIELD_NOUNS,
    # Cache Document Fields
    CACHE_FIELD_TITLE_QUERY, CACHE_FIELD_START_DATE_QUERY, CACHE_FIELD_END_DATE_QUERY,
    CACHE_FIELD_TAGS_QUERY, CACHE_FIELD_TOP_N, CACHE_FIELD_TOP_WORDS
)

# 💡 [수정] 순환 참조를 피하기 위해 run_extraction_and_save_to_category_nouns 함수를 가져옵니다.
# from .importer import run_extraction_and_save_to_category_nouns
# 하지만 파이썬 모듈 구조상, calculate_and_save_top_nouns가 importer를 호출하는 경우
# 이 파일에서 from .importer import ... 를 직접 호출하는 것이 가장 일반적입니다.
# 만약 .importer가 .cache_manager를 호출한다면 순환 참조가 발생하지만, 현재는 그렇지 않으므로 직접 호출하겠습니다.

# 🚨 이 파일은 cache_manager.py 이므로, importer.py의 함수를 직접 가져옵니다.
try:
    from .importer import run_extraction_and_save_to_category_nouns
except ImportError:
    # 모듈 구조에 문제가 있을 경우를 대비한 대체 처리
    def run_extraction_and_save_to_category_nouns():
        print("경고: importer 모듈을 로드할 수 없습니다. DB 업데이트 기능을 건너뜁니다.")
        return False  # 실패를 나타냄


def get_top_nouns_from_cache(query_conditions: Dict[str, Any], top_n: int = TOP_N) -> Optional[
    List[Dict[str, Any]]]:
    """
    주어진 조건 딕셔너리와 top_n에 해당하는 결과를 캐시 컬렉션에서 조회합니다.
    """
    client = get_mongodb_client()
    if not client:
        return None

    db = client[DB_NAME]
    cache_collection = db[TOP_NOUNS_CACHE_COLLECTION]

    # query_conditions 딕셔너리에서 값 추출 (없는 경우 빈 문자열 또는 None 처리)
    title = query_conditions.get('title', "")
    tags = query_conditions.get('tags', None)
    start_date = query_conditions.get('start_date', "")
    end_date = query_conditions.get('end_date', "")

    # tags를 쉼표로 구분된 문자열로 변환하여 캐시 키로 사용
    tags_key = ",".join(tags) if tags else ""

    # 캐시 키 구성 (완전 일치 검색)
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
        print(f"✅ 캐시에서 Title='{title}', Tags='{tags_key}', Date='{start_date}~{end_date}' (Top {top_n}) 데이터를 찾았습니다.")
        return cached_doc.get(CACHE_FIELD_TOP_WORDS)

    print(
        f"❌ 캐시에 Title='{title}', Tags='{tags_key}', Date='{start_date}~{end_date}' (Top {top_n}) 데이터가 없습니다. 새로 생성합니다.")
    return None


def calculate_and_save_top_nouns(query_conditions: Dict[str, Any], top_n: int = TOP_N) -> Optional[
    List[Dict[str, Any]]]:
    """
    'file_noun_records'에서 조건을 만족하는 레코드를 검색하고,
    명사 빈도수를 계산하여 상위 N개를 캐시에 저장합니다.
    """
    client = get_mongodb_client()
    if not client:
        return None

    db = client[DB_NAME]
    record_collection = db[RECORD_NOUNS_COLLECTION]
    cache_collection = db[TOP_NOUNS_CACHE_COLLECTION]

    # query_conditions 딕셔너리에서 값 추출
    title = query_conditions.get('title', "")
    tags = query_conditions.get('tags', None)
    start_date = query_conditions.get('start_date', "")
    end_date = query_conditions.get('end_date', "")

    # 검색 조건을 MongoDB 쿼리 형태로 변환
    def build_query(t, tg, sd, ed) -> Dict[str, Any]:
        q: Dict[str, Any] = {}
        if t:
            q[DB_FIELD_HEADING] = {"$regex": t, "$options": "i"}
        if tg:
            q[DB_FIELD_TAGS] = {"$in": tg}
        date_query = {}
        if sd:
            date_query["$gte"] = sd
        if ed:
            date_query["$lte"] = ed
        if date_query:
            q[DB_FIELD_DATE] = date_query
        return q

    # 1차 검색 시도 (현재 DB 상태)
    current_query = build_query(title, tags, start_date, end_date)
    print(f"🔍 '{RECORD_NOUNS_COLLECTION}'에서 조건 ({current_query})에 맞는 레코드 검색 중...")
    matching_records = list(record_collection.find(current_query, {DB_FIELD_NOUNS: 1, "_id": 0}))

    # 💡 [수정] 조건에 맞는 레코드가 없을 경우 Importer를 실행하여 DB 업데이트 후 재시도
    if not matching_records:
        print(f"⚠️ 경고: 조건 ({current_query})에 맞는 레코드가 '{RECORD_NOUNS_COLLECTION}'에 없습니다. CSV 업데이트를 시도합니다.")

        # Importer 실행 (CSV를 다시 읽고 명사 추출 후 DB 덮어쓰기)
        run_extraction_and_save_to_category_nouns()

        # 업데이트 후 2차 검색 시도
        matching_records = list(record_collection.find(current_query, {DB_FIELD_NOUNS: 1, "_id": 0}))

        if not matching_records:
            client.close()
            # 2차 검색에서도 레코드가 없다면 최종적으로 빈 배열 반환
            print(f"⚠️ 경고: CSV 업데이트 후에도 조건 ({current_query})에 맞는 레코드가 '{RECORD_NOUNS_COLLECTION}'에 없습니다. 빈 결과를 반환합니다.")
            return []

        print(f"✅ CSV 업데이트 후 조건 ({current_query})에 맞는 레코드 {len(matching_records)}개를 찾았습니다.")

    # 2. 명사 종합 및 빈도수 계산
    all_nouns = []
    for record in matching_records:
        all_nouns.extend(record.get(DB_FIELD_NOUNS, []))

    noun_counts = Counter(all_nouns)
    top_n_words = noun_counts.most_common(top_n)

    top_words_for_db = [
        {"word": word, "count": count} for word, count in top_n_words
    ]

    print(f"✅ 총 {len(matching_records)}개 레코드에서 명사 추출 및 상위 {top_n}개 계산 완료.")

    # 3. 새로운 MongoDB 컬렉션에 저장 (캐시)
    tags_key = ",".join(tags) if tags else ""

    # 캐시 문서 구성 (캐시 키에 사용된 값 저장)
    cache_document = {
        CACHE_FIELD_TITLE_QUERY: title,
        CACHE_FIELD_TAGS_QUERY: tags_key,
        CACHE_FIELD_START_DATE_QUERY: start_date,
        CACHE_FIELD_END_DATE_QUERY: end_date,
        CACHE_FIELD_TOP_N: top_n,
        "total_records": len(matching_records),
        CACHE_FIELD_TOP_WORDS: top_words_for_db
    }

    # 캐시 쿼리 구성 (완전 일치 검색)
    cache_query = {
        CACHE_FIELD_TITLE_QUERY: title,
        CACHE_FIELD_TAGS_QUERY: tags_key,
        CACHE_FIELD_START_DATE_QUERY: start_date,
        CACHE_FIELD_END_DATE_QUERY: end_date,
        CACHE_FIELD_TOP_N: top_n
    }

    cache_collection.replace_one(cache_query, cache_document, upsert=True)

    print(f"✅ 상위 명사 결과가 '{TOP_NOUNS_CACHE_COLLECTION}' 컬렉션에 성공적으로 저장되었습니다.")
    client.close()

    return top_words_for_db


def get_top_nouns_for_conditions(query_conditions: Dict[str, Any], top_n: int = TOP_N) -> Optional[
    List[Dict[str, Any]]]:
    """
    메인 진입 함수: 캐시 확인 후, 없으면 계산 및 저장 후 결과를 반환합니다.
    """
    # query_conditions에서 값 추출
    title = query_conditions.get('title')
    tags = query_conditions.get('tags')
    start_date = query_conditions.get('start_date')
    end_date = query_conditions.get('end_date')

    # None 값을 빈 문자열 또는 None으로 대체 (캐시 키 생성 및 로직 사용을 위해)
    tt = title if title is not None else ""
    tg = tags if tags is not None else None
    sd = start_date if start_date is not None else ""
    ed = end_date if end_date is not None else ""

    # 캐시 함수에 전달할 조건을 재구성
    processed_conditions = {
        'title': tt,
        'tags': tg,
        'start_date': sd,
        'end_date': ed,
    }

    tags_log = ", ".join(tg) if tg else '전체'
    print(f"\n--- 상위 명사 추출 시작: Title='{tt}', Tags='{tags_log}', Date Range='{sd} ~ {ed}', Top N={top_n} ---")

    # 1. 캐시에서 조건에 맞는 파일이 있는지 먼저 확인
    result = get_top_nouns_from_cache(processed_conditions, top_n)

    if result is not None:
        return result

    # 2. 캐시에 없다면, 계산 및 저장 후 결과를 반환
    result = calculate_and_save_top_nouns(processed_conditions, top_n)

    return result