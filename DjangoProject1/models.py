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
    @staticmethod
    def save(filepath):
        filename = os.path.basename(filepath)
        if db.fs.files.find_one({'filename': filename}):
            print(f"이미 원본 파일 '{filename}'이 DB에 존재합니다.")
            return db.fs.files.find_one({'filename': filename})['_id']
        with open(filepath, 'rb') as f:
            file_id = fs.put(f, filename=filename)
            print(f"📜 원본 파일 '{filename}'을 DB(GridFS)에 보관했습니다.")
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
    def __init__(self, analysis_data, source_filename=None):
        self.analysis_data = analysis_data
        self.source_filename = source_filename

    def save(self):
        doc = {'source_filename': self.source_filename, 'analysis_data': self.analysis_data}
        result = db.analyzed_texts.insert_one(doc)
        print(f"✅ 분석된 데이터('{self.source_filename}')가 DB에 성공적으로 저장되었습니다.")
        return result.inserted_id

    @staticmethod
    def find_by_filename(filename):
        return db.analyzed_texts.find_one({'source_filename': filename})

    @staticmethod
    def generate_report_files(document, output_dir='.'):
        """
        DB에서 읽어온 '문서'를 기반으로 결과 파일을 생성합니다.
        """
        if not document:
            print("-> 파일 생성을 위한 데이터가 없어 건너뜁니다.")
            return

        analysis_data = document.get('analysis_data', {})
        source_filename = document.get('source_filename', '원본 파일 정보 없음')

        output_content = f"--- '{source_filename}' 분석 결과 ---\n\n"
        output_content += f"전체 단어 수: {analysis_data.get('total_word_count', 0)}\n"
        output_content += f"고유 단어 수: {analysis_data.get('unique_word_count', 0)}\n"
        output_content += "\n--- 단어별 빈도수 ---\n"

        if 'frequency' in analysis_data:
            for word, count in analysis_data['frequency'].items():
                output_content += f"{word} : {count}\n"
        else:
            output_content += "빈도수 정보가 없습니다.\n"

        # 실제 파일로 "배출"하는 부분
        output_filepath = os.path.join(output_dir, "output.txt")
        os.makedirs(output_dir, exist_ok=True)
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"-> 📄 'output.txt' 파일이 성공적으로 배출되었습니다: {output_filepath}")


def process_article(filepath):
    """
    하나의 텍스트 파일을 순서도 로직에 따라 지능적으로 처리하여,
    최종 분석 결과를 '반환'합니다.
    """
    filename = os.path.basename(filepath)
    print("\n" + "-" * 50)
    print(f"▶️ '{filename}' 파일 처리 시작...")
    existing_analysis = AnalyzedText.find_by_filename(filename)
    if existing_analysis:
        print("-> ✅ 발견! 기존 분석 결과를 사용합니다.")
        return existing_analysis
    print("-> ❌ 없음. DB에 보관된 원본 파일을 검색합니다...")
    archived_content = OriginalFile.read_content_by_filename(filename)
    if archived_content:
        print("-> ✅ 발견! DB 원본으로 새로운 분석을 생성합니다.")
        processed_data = analyze_text(archived_content)
        new_analysis = AnalyzedText(processed_data, filename)
        new_analysis_id = new_analysis.save()
        return AnalyzedText.find_by_filename(filename)  # 저장 후 다시 찾아 반환
    print("-> ❌ 없음. 로컬 파일을 읽어 처음부터 처리합니다.")
    if not os.path.exists(filepath):
        print(f"-> ❌ 오류! 로컬 경로에도 파일이 없습니다.")
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        local_content = f.read()
    OriginalFile.save(filepath)
    processed_data = analyze_text(local_content)
    new_analysis = AnalyzedText(processed_data, filename)
    new_analysis_id = new_analysis.save()
    return AnalyzedText.find_by_filename(filename)  # 저장 후 다시 찾아 반환


# --- 이 파일을 직접 실행할 경우에만 아래 코드가 동작 ---
if __name__ == "__main__":

    def run_intelligent_processing_test():
        # --- 테스트 설정 ---
        test_filepath = r"C:\Users\슈퍼컴\Desktop\text file\test.txt"
        report_dir = r"C:\Users\슈퍼컴\Desktop\outt"  # Output 파일을 배출할 폴더

        print("\n" + "=" * 50)
        print("🚀 지능형 처리 및 Output 파일 배출 테스트를 시작합니다.")
        print("=" * 50)

        try:
            db.analyzed_texts.delete_many({})
            db.fs.files.delete_many({})
            db.fs.chunks.delete_many({})
            print("-> 테스트 환경 초기화 완료.")


            # --- 시나리오 1: 완전히 새로운 파일 처리 ---
            print("\n\n--- [시나리오 1] 새로운 파일 처리 ---")
            result_doc_1 = process_article(test_filepath)
            AnalyzedText.generate_report_files(result_doc_1, report_dir)

            # --- 시나리오 2: 이미 분석 결과가 있는 파일 처리 ---
            print("\n\n--- [시나리오 2] 이미 분석된 파일 처리 ---")
            result_doc_2 = process_article(test_filepath)
            AnalyzedText.generate_report_files(result_doc_2, report_dir)

            # --- 시나리오 3: 원본만 있고 분석 결과는 없는 파일 처리 ---
            print("\n\n--- [시나리오 3] 원본만 보관된 파일 처리 ---")
            db.analyzed_texts.delete_many({})
            print("-> (상황 조작: 분석 결과만 삭제됨)")
            result_doc_3 = process_article(test_filepath)
            AnalyzedText.generate_report_files(result_doc_3, report_dir)

        except Exception as e:
            print(f"❌ 테스트 중 오류 발생: {e}")
        finally:
            # --- 테스트 뒷정리 ---
            #if os.path.exists(test_filepath): os.remove(test_filepath)
            print(f"\n\n✨ 모든 테스트가 완료되었습니다. 결과는 '{report_dir}' 폴더를 확인하세요.")


    run_intelligent_processing_test()