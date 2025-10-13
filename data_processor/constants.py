# data_processor/constants.py
import os

# <username>과 <password>를 정확히 입력
# MONGO_HOST: Docker Compose 서비스 이름 'db'를 사용하도록 기본값을 설정
MONGO_HOST = os.environ.get('MONGO_HOST', 'db')
MONGO_PORT = os.environ.get('MONGO_PORT', '27017')
DB_NAME = os.environ.get('MONGO_DB', 'BBC_analysis_db') # DB 이름도 환경 변수 우선
MONGO_USER = os.environ.get('MONGO_USER', 'mongouser') # 하드코딩된 값을 환경 변수 우선으로 변경
MONGO_PASS = os.environ.get('MONGO_PASS', '1234')

# ----------------------------------------------------------------------
# MONGO_URI 구성 (동적 생성)
# ----------------------------------------------------------------------
# 🌟 MONGO_HOST 변수를 사용하여 URI를 완성합니다.
MONGO_URI = (
    f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{DB_NAME}"
    "?authSource=admin"
)

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