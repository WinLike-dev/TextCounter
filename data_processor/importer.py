# data_processor/importer.py

from typing import List
import pandas as pd
from textblob import TextBlob
from .db_connector import get_mongodb_client
from .constants import DB_NAME, CATEGORY_COLLECTION, FILE_PATH, EXCLUDE_NOUNS
import warnings

warnings.filterwarnings('ignore')


def extract_and_filter_proper_nouns(text) -> List[str]:
    """TextBlob을 사용하여 고유 명사를 추출하고, 제외 목록에 있는 단어를 필터링합니다. (filtering.py 로직)"""
    if pd.isna(text) or text is None:
        return []

    text = str(text).replace('\n', ' ')

    try:
        blob = TextBlob(text)
        # NNP/NNPS 태그된 단어 중 제외 목록을 거르고, 길이 1 또는 숫자인 단어를 제거
        filtered_nouns = [
            word.lower()
            for word, tag in blob.tags
            if tag in ('NNP', 'NNPS') and
               word.lower() not in EXCLUDE_NOUNS and
               len(word) > 1 and not word.isdigit()
        ]

        return filtered_nouns
    except Exception as e:
        print(f"ERROR: TextBlob 처리 중 오류 발생: {e}")
        return []


def run_extraction_and_save_to_category_nouns():
    """CSV에서 명사를 추출하고 'category_nouns' (ImFiles) 컬렉션에 바로 저장합니다."""
    client = get_mongodb_client()
    if not client:
        return

    try:
        df = pd.read_csv(FILE_PATH, sep='\t')
    except FileNotFoundError:
        print(f"ERROR: 파일을 찾을 수 없습니다: {FILE_PATH}. 경로({FILE_PATH})를 확인하세요.")
        client.close()
        return

    db = client[DB_NAME]
    category_collection = db[CATEGORY_COLLECTION]
    category_collection.delete_many({})

    grouped = df.groupby('category')
    documents_to_insert = []

    print("--- ImFiles 생성 및 MongoDB 직접 저장 시작 ---")

    for category, group in grouped:
        combined_text = ' '.join(group['title'].astype(str) + ' ' + group['content'].astype(str))
        nouns = extract_and_filter_proper_nouns(combined_text)

        document = {
            "category": category,
            "nouns": nouns,
            "total_count": len(nouns)
        }
        documents_to_insert.append(document)
        print(f" - [{category.upper()}] {len(nouns)}개의 명사 추출 완료.")

    if documents_to_insert:
        category_collection.insert_many(documents_to_insert)
        print(f"\n✅ 모든 ImFiles 데이터가 '{CATEGORY_COLLECTION}' 컬렉션에 성공적으로 저장되었습니다.")

    client.close()