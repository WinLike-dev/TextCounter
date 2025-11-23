# data_processor/importer.py

from typing import List
import pandas as pd
from textblob import TextBlob
from .db_connector import get_mongodb_client
from .constants import (
    DB_NAME, RECORD_NOUNS_COLLECTION, FILE_FOLDER_PATH, EXCLUDE_NOUNS,
    DB_FIELD_MAPPING, DB_FIELD_DEFAULTS,
    # DB Document Fields
    DB_FIELD_HEADING, DB_FIELD_DATE, DB_FIELD_TAGS, DB_FIELD_ARTICLES,
    DB_FIELD_NOUNS, DB_FIELD_RECORD_ID
)
import warnings
import os

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


def parse_tags(tags_str: str) -> List[str]:
    """문자열 형태의 태그 목록을 파싱하여 소문자 리스트로 반환합니다."""
    if not tags_str:
        return DB_FIELD_DEFAULTS.get(DB_FIELD_TAGS, [])

    # 대괄호와 따옴표 제거 후 쉼표로 분리하여 공백을 제거
    tags_str = tags_str.strip().strip('[]').replace("'", "")
    if not tags_str:
        return DB_FIELD_DEFAULTS.get(DB_FIELD_TAGS, [])

    return [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]


def run_extraction_and_save_to_category_nouns():
    """
    CSV 파일을 읽어 각 레코드의 명사를 추출하고, MongoDB의 'file_noun_records' 컬렉션에 저장합니다.
    """
    client = get_mongodb_client()
    if client is None:
        return

    # 💡 [수정] 디렉토리 내 모든 CSV 파일 처리 로직
    # 1. 'data' 폴더에서 모든 CSV 파일 경로를 찾습니다.
    csv_files = [
        os.path.join(FILE_FOLDER_PATH, f)
        for f in os.listdir(FILE_FOLDER_PATH)
        if f.endswith('.csv')
    ]

    if not csv_files:
        print(f"ERROR: 폴더 '{FILE_FOLDER_PATH}'에 처리할 CSV 파일이 없습니다.")
        client.close()
        return

    all_dataframes = []

    try:
        # 2. 각 CSV 파일을 읽어 DataFrame 리스트에 추가합니다.
        for file_path in csv_files:
            print(f"🔄 파일 로드 중: {file_path}")
            # 파일 로드
            df_chunk = pd.read_csv(file_path, encoding='utf-8')
            all_dataframes.append(df_chunk)

        # 3. 모든 DataFrame을 하나로 병합합니다.
        df = pd.concat(all_dataframes, ignore_index=True)
        print(f"✅ 총 {len(csv_files)}개 파일 로드 완료. 전체 레코드: {len(df)}")


        # CSV 컬럼과 DB 필드 이름 매핑
        df = df.rename(columns={
            csv_col: db_col
            for csv_col, db_col in DB_FIELD_MAPPING.items()
            if csv_col in df.columns
        })

        # 필수 컬럼 검사
        required_db_cols = list(DB_FIELD_MAPPING.values())
        if not all(col in df.columns for col in required_db_cols):
            missing = [col for col in required_db_cols if col not in df.columns]
            raise ValueError(f"필수 컬럼 누락: {missing}. CSV 컬럼과 DB_FIELD_MAPPING을 확인하세요.")

        # 데이터 정리 및 타입 변환 (상수 사용)
        df[DB_FIELD_DATE] = pd.to_datetime(df[DB_FIELD_DATE], errors='coerce').dt.strftime('%Y-%m-%d')
        df[DB_FIELD_ARTICLES] = df[DB_FIELD_ARTICLES].fillna('')
        df[DB_FIELD_HEADING] = df[DB_FIELD_HEADING].fillna('')
        df[DB_FIELD_TAGS] = df[DB_FIELD_TAGS].fillna('')

        # MongoDB에 저장할 때 사용할 고유 식별자(index)를 추가 (상수 사용)
        df[DB_FIELD_RECORD_ID] = df.index

    except Exception as e:
        print(f"ERROR: 데이터 처리 중 오류 발생: {e}")
        client.close()
        return

    db = client[DB_NAME]
    record_collection = db[RECORD_NOUNS_COLLECTION]
    record_collection.delete_many({})  # 기존 데이터 삭제

    documents_to_insert = []
    total_records = len(df)

    print("--- 레코드별 명사 추출 및 MongoDB 직접 저장 시작 (file_noun_records) ---")

    for index, row in df.iterrows():
        # Heading과 Articles를 결합하여 명사 추출 (상수 사용)
        combined_text = str(row[DB_FIELD_HEADING]) + ' ' + str(row[DB_FIELD_ARTICLES])
        nouns = extract_and_filter_proper_nouns(combined_text)

        # Tags 파싱 (상수 사용)
        parsed_tags = parse_tags(str(row[DB_FIELD_TAGS]))

        # 🌟 상수 사용 🌟
        document = {
            DB_FIELD_RECORD_ID: int(row[DB_FIELD_RECORD_ID]),
            DB_FIELD_HEADING: str(row[DB_FIELD_HEADING]),
            DB_FIELD_DATE: str(row[DB_FIELD_DATE]),
            DB_FIELD_TAGS: parsed_tags,
            DB_FIELD_NOUNS: nouns,
            "noun_count": len(nouns)  # noun_count는 그대로 사용
        }
        documents_to_insert.append(document)

        # 진행 상황 출력
        if (index + 1) % 1000 == 0:
            print(f"처리 진행 중: {index + 1}/{total_records} 레코드")

    if documents_to_insert:
        record_collection.insert_many(documents_to_insert)
        print(f"✅ 총 {len(documents_to_insert)}개 레코드를 '{RECORD_NOUNS_COLLECTION}'에 성공적으로 저장했습니다.")
    else:
        print("⚠️ 경고: 저장할 레코드가 없습니다.")

    client.close()


if __name__ == '__main__':
    run_extraction_and_save_to_category_nouns()