# data_processor/cache_manager.py

from collections import Counter
from typing import List, Tuple
import pandas as pd
from .db_connector import get_mongodb_client
from .constants import DB_NAME, CATEGORY_COLLECTION, OUTPUT_COLLECTION, TOP_N


def get_top_words_and_manage_cache(category: str, force_reprocess: bool = False) -> List[Tuple[str, int]]:
    """
    output_files 캐시를 확인하고, 없거나 강제 재생성 요청 시 ImFiles에서 처리 후 캐시합니다.
    """
    client = get_mongodb_client()
    if not client:
        return []

    db = client[DB_NAME]
    output_col = db[OUTPUT_COLLECTION]
    category_col = db[CATEGORY_COLLECTION]

    # 1. 캐시 확인
    cached_data = output_col.find_one({"category": category})
    if cached_data and not force_reprocess:
        client.close()
        return [(item['word'], item['count']) for item in cached_data['top_words']]

    # 2. 캐시 미스: ImFiles(category_nouns)에서 원본 데이터 조회
    raw_data = category_col.find_one({"category": category})

    if not raw_data or 'nouns' not in raw_data:
        client.close()
        return []

    all_nouns = raw_data['nouns']

    # 3. 빈도수 계산 및 상위 N개 선택
    word_counts = Counter(all_nouns)
    top_words = word_counts.most_common(TOP_N)

    # 기존 캐시 삭제 후 새로 저장
    output_col.delete_one({"category": category})

    cache_document = {
        "category": category,
        "top_words": [{"word": word, "count": count} for word, count in top_words],
        "created_at": pd.Timestamp.now().isoformat()
    }
    output_col.insert_one(cache_document)

    client.close()
    return top_words