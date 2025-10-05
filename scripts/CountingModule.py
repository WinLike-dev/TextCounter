
import re
from collections import Counter
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure



MONGO_URI = ""  # MongoDB 서버 주소
DB_NAME = ""       # 사용할 데이터베이스 이름
IM_COLLECTION = ""     # 중간 파일(IM)이 저장된 컬렉션
FINAL_COLLECTION = ""   # 최종 단어 수 결과를 저장할 컬렉션

def connect_to_mongodb():
    """
    DB연결 및 컬렉션 객체 반환.
    DB연결 실패시 프로그램 종료.

    """
    try:
        client = MongoClient(MONGO_URI)
        # 서버 연결 확인
        client.admin.command('ping')
        print("DB 연결 완료")
        db = client[DB_NAME]
        return db[IM_COLLECTION], db[FINAL_COLLECTION]
    except ConnectionFailure as e:
        print(f"DB 연결 실패: {e}")
        exit() # 프로그램 종료

def perform_word_count(text_content):
    """
    텍스트 내용의 단어 수를 계산
    - 텍스트를 소문자로 변환.
    - 정규표현식을 사용해 영어 단어만 추출.
    - 단어의 빈도를 계산해 딕셔너리 형태로 반환.

    """
    if not isinstance(text_content, str):
        return {}

    # 텍스트를 소문자로 변환
    text = text_content.lower()
    # 정규표현식을 사용하여 단어(알파벳)만 추출
    words = re.findall(r'\b[a-z]+\b', text)
    # Counter를 사용하여 단어 빈도수 계산
    word_counts = Counter(words)
    return dict(word_counts)

def process_files(im_collection, final_collection):
    """
    IM 컬렉션에서 처리되지 않은 파일을 가져와 단어 수를 세고,
    결과를 FINAL 컬렉션에 저장한 뒤, 원본 파일의 상태를 업데이트.
    """
    # 'status' 필드가 'processed'가 아닌 문서를 찾음.
    # 이 필드는 데이터 필터링 모듈에서 파일을 저장할 때 'unprocessed' 등으로 설정해주어야 함.
    files_to_process = im_collection.find({"status": {"$ne": "processed"}})

    processed_count = 0
    for im_file in files_to_process:
        file_id = im_file["_id"]
        file_name = im_file.get("filename", "N/A") # 파일 이름이 없는 경우 대비
        content = im_file.get("content", "")       # 내용이 없는 경우 대비

        print(f"파일 처리 시작: {file_name} (ID: {file_id})")

        # 단어 수 계산 수행
        word_counts = perform_word_count(content)

        if not word_counts:
            print(f"-> 내용이 없거나 처리할 단어가 없어 건너뜁니다.")

            im_collection.update_one({"_id": file_id}, {"$set": {"status": "processed_empty"}})
            continue

        # 최종 결과를 저장할 문서 생성
        final_document = {
            "source_file_id": file_id,
            "source_filename": file_name,
            "word_counts": word_counts
        }

        # 최종 결과를 DB에 저장
        # 동일한 파일에 대한 결과가 이미 있는지 확인하고, 있다면 업데이트, 없다면 새로 추가 (upsert)
        final_collection.update_one(
            {"source_file_id": file_id},
            {"$set": final_document},
            upsert=True
        )
        print(f"-> 단어 수 계산 완료. 최종 결과를 DB에 저장/업데이트했습니다.")

        # 원본 IM 파일의 상태를 'processed'로 업데이트하여 중복 작업을 방지
        im_collection.update_one({"_id": file_id}, {"$set": {"status": "processed"}})
        print(f"-> 원본 파일 상태를 'processed'로 업데이트했습니다.")
        processed_count += 1

    if processed_count == 0:
        print("\n처리할 새로운 중간 파일(IM file)이 없습니다.")
    else:
        print(f"\n총 {processed_count}개의 파일 처리를 완료했습니다.")


if __name__ == "__main__":
    # 1. MongoDB 연결
    im_collection, final_collection = connect_to_mongodb()

    # 2. 파일 처리 로직 실행
    process_files(im_collection, final_collection)
