# data_processor/constants.py


# <username>과 <password>를 정확히 입력
MONGO_URI = "mongodb://mongouser:1234@localhost:27017/?authSource=admin"
DB_NAME = "BBC_analysis_db"

# ----------------------------------------------------------------------
# 컬렉션 및 파일 경로 설정
# ----------------------------------------------------------------------
CATEGORY_COLLECTION = "ImFiles"  # ImFiles (원본 명사 리스트)
OUTPUT_COLLECTION = "output_files"      # OutputFiles (최종 빈도 캐시)
FILE_PATH = "data/bbc-news-data.csv"    # CSV 파일 경로 (프로젝트 루트 기준)
TOP_N = 20 # 상위 단어 개수

# ----------------------------------------------------------------------
# 고유 명사 추출 제외 목록
# ----------------------------------------------------------------------
EXCLUDE_NOUNS = {
    'mr', 'mrs', 'ms', 'dr', 'prof', 'lord', 'sir', 'madam', 'hon',
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
    'september', 'october', 'november', 'december',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    'group', 'company', 'year', 'day', 'week', 'month', 'world', 'us', 'uk', 'eu',
    'time', 'service', 'minister', 'government'
}