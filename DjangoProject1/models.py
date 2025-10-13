from gridfs import GridFS
from pymongo import MongoClient
import os
from collections import Counter

# --- 데이터베이스 및 분석 엔진 설정 (이전과 동일) ---
client = MongoClient('mongodb://localhost:27017/')
db = client['text_counting_project']
fs = GridFS(db)


def analyze_text(text_content):
    if not isinstance(text_content, str): return {}
    words = text_content.split()
    frequency = Counter(words)
    return {
        'total_word_count': len(words),
        'unique_word_count': len(frequency),
        'frequency': dict(frequency.most_common()),
        'status': 'analysis_completed'
    }


class OriginalFile:
    """ "원본 서류 보관함" 역할: 원본 파일을 GridFS에 저장하고 읽어옵니다. """
    @staticmethod
    def save(filepath):
        filename = os.path.basename(filepath)
        if db.fs.files.find_one({'filename': filename}):
            print(f"이미 원본 파일 '{filename}'이 DB에 존재합니다.")
            return db.fs.files.find_one({'filename': filename})['_id']
        with open(filepath, 'rb') as f:
            file_id = fs.put(f, filename=filename)
            print(f"원본 파일 '{filename}'을 DB(GridFS)에 보관했습니다.")
            return file_id

    @staticmethod
    def read_content_by_filename(filename):
        try:
            grid_out = fs.find_one({'filename': filename})
            if grid_out:
                return grid_out.read().decode('utf-8')
            return None
        except Exception as e:
            print(f"GridFS에서 파일 읽기 오류: {e}")
            return None


class AnalyzedText:
    """ "분석 보고서 보관함" 역할: 분석된 결과를 저장하고 읽어옵니다. """

    def __init__(self, analysis_data, source_filename=None):
        self.analysis_data = analysis_data
        self.source_filename = source_filename

    def save(self):
        doc = {'source_filename': self.source_filename, 'analysis_data': self.analysis_data}
        result = db.analyzed_texts.insert_one(doc)
        print(f"분석된 데이터('{self.source_filename}')가 DB에 성공적으로 저장되었습니다.")
        return result.inserted_id

    @staticmethod
    def find_by_filename(filename):
        return db.analyzed_texts.find_one({'source_filename': filename})


def process_article(filepath):
    filename = os.path.basename(filepath)
    print("\n" + "-" * 50)
    print(f"'{filename}' 파일 처리 시작...")

    # 1.  이미 분석된 Output이 있는지 확인합니다.
    print("1. 기존 분석 결과(Output)를 검색합니다...")
    existing_analysis = AnalyzedText.find_by_filename(filename)
    if existing_analysis:
        print("-> 발견! 기존 분석 결과를 사용합니다. (작업 종료)")
        return existing_analysis

    # 2. output 없다면, IM이 저장되어 있는지 확인
    print("-> 없음. 다음으로 DB에 보관된 원본 파일(IM)을 검색합니다...")
    archived_content = OriginalFile.read_content_by_filename(filename)
    if archived_content:
        print("->  발견! DB에 보관된 원본 파일을 바탕으로 새로운 분석을 생성합니다.")
        # DB에서 읽은 내용으로 분석을 수행합니다.
        processed_data = analyze_text(archived_content)
        # 분석 결과를 모델에 담아 DB에 저장합니다.
        new_analysis = AnalyzedText(processed_data, filename)
        new_analysis.save()
        return new_analysis

    # 3. 둘다 없는 경우 새롭게 output, im파일 생성
    print("-> 없음. 이것은 완전히 새로운 파일입니다. 처음부터 모든 작업을 시작합니다.")
    if not os.path.exists(filepath):
        print(f"-> 오류! 로컬 경로에도 '{filepath}' 파일이 없습니다. (작업 종료)")
        return None

    # 로컬 파일을 읽습니다.
    with open(filepath, 'r', encoding='utf-8') as f:
        local_content = f.read()

    # (선택사항이지만 좋은 습관) 원본을 DB에 보관(Archive)합니다.
    OriginalFile.save(filepath)

    # 내용을 분석합니다.
    processed_data = analyze_text(local_content)

    # 분석 결과를 DB에 저장합니다.
    new_analysis = AnalyzedText(processed_data, filename)
    new_analysis.save()
    return new_analysis




# --- 이 파일을 직접 실행할 경우에만 아래 코드가 동작 ---
if __name__ == "__main__":

    def run_intelligent_processing_test():
        test_filepath = r"C:\Users\슈퍼컴\Desktop\text file\test2.txt"

        print("\n" + "=" * 50)
        print("데이터 베이스 시나리오 테스트를 시작합니다.")
        print("=" * 50)

        # db초기화부분
        os.makedirs(os.path.dirname(test_filepath), exist_ok=True)
        # 테스트를 위해 이전 기록 삭제
        db.analyzed_texts.delete_many({})
        db.fs.files.delete_many({})
        db.fs.chunks.delete_many({})
        print("-> 테스트 환경 초기화 완료.")

        # --- 시나리오 1: 완전히 새로운 파일 처리 ---
        print("\n\n--- [시나리오 1] 새로운 파일 처리 ---")
        process_article(test_filepath)

        # --- 시나리오 2: 이미 분석 결과가 있는 파일 처리 ---
        print("\n\n--- [시나리오 2] 이미 분석된 파일 처리 ---")
        process_article(test_filepath)

        # --- 시나리오 3: 원본만 있고 분석 결과는 없는 파일 처리 ---
        print("\n\n--- [시나리오 3] 원본만 보관된 파일 처리 ---")
        # 시나리오 3을 위해 인위적으로 분석 결과만 삭제
        db.analyzed_texts.delete_many({})
        print("-> (상황 조작: 분석 결과만 삭제됨)")
        process_article(test_filepath)

        # --- 테스트 뒷정리 ---
        # test파일 삭제 하는 부분
        #if os.path.exists(test_filepath): os.remove(test_filepath)
        print("\n\n 모든 테스트가 완료되었습니다.")


    run_intelligent_processing_test()