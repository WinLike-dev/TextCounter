# data_processor/constants.py

import os

# <username>과 <password>를 정확히 입력
# MONGO_HOST: Docker Compose 서비스 이름 'db'를 사용하도록 기본값을 설정
MONGO_HOST = os.environ.get('MONGO_HOST', 'db')
MONGO_PORT = os.environ.get('MONGO_PORT', '27017')
DB_NAME = os.environ.get('MONGO_DB', 'BBC_analysis_db')
MONGO_USER = os.environ.get('MONGO_USER', 'mongouser')
MONGO_PASS = os.environ.get('MONGO_PASS', '1234')

# ----------------------------------------------------------------------
# MONGO_URI 구성
# ----------------------------------------------------------------------
MONGO_URI = (
    f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{DB_NAME}"
    "?authSource=admin"
)

# ----------------------------------------------------------------------
# 컬렉션 및 파일 경로 설정
# ----------------------------------------------------------------------
RECORD_NOUNS_COLLECTION = "file_noun_records"
TOP_NOUNS_CACHE_COLLECTION = "top_nouns_cache"

FILE_FOLDER_PATH = "data"
TOP_N = 50

# ----------------------------------------------------------------------
# 🌟 MongoDB 문서 필드 스키마 정의 🌟
# ----------------------------------------------------------------------
# record_nouns (원본 데이터 및 명사 포함) 컬렉션의 필드 이름
DB_FIELD_HEADING = 'Heading'
DB_FIELD_DATE = 'Date'
DB_FIELD_TAGS = 'Tags'
DB_FIELD_ARTICLES = 'Articles'
DB_FIELD_NOUNS = 'nouns'
DB_FIELD_RECORD_ID = 'record_id'

# top_nouns_cache (캐시) 컬렉션의 필드 이름 (검색 조건)
CACHE_FIELD_TITLE_QUERY = 'Title'
CACHE_FIELD_START_DATE_QUERY = 'StartDate'
CACHE_FIELD_END_DATE_QUERY = 'EndDate'
CACHE_FIELD_TAGS_QUERY = 'Tags'
CACHE_FIELD_TOP_N = 'top_n'
CACHE_FIELD_TOP_WORDS = 'top_words'


# ----------------------------------------------------------------------
# CSV 파일 구조 및 DB 매핑 설정 (importer.py에서 사용)
# ----------------------------------------------------------------------

# 1. New CSV File Columns (읽어들일 CSV 파일의 필수 열 목록)
CSV_COLUMNS_SOURCE = ['title', 'text', 'timestamp', 'tags']

# 2. Mapping from CSV Column Name (Key) to Target DB Field Name (Value)
DB_FIELD_MAPPING = {
    'title': DB_FIELD_HEADING,
    'text': DB_FIELD_ARTICLES,
    'timestamp': DB_FIELD_DATE,
    'tags': DB_FIELD_TAGS,
}

# 3. Default Values for Fields Missing in CSV but required for Analysis/DB
DB_FIELD_DEFAULTS = {
    DB_FIELD_TAGS: [], # Tags 필드의 기본값 (리스트)
}

# ----------------------------------------------------------------------
# 고유 명사 추출 제외 목록
# ----------------------------------------------------------------------
EXCLUDE_NOUNS = {
    'mr', 'mrs', 'ms', 'dr', 'prof', 'lord', 'sir', 'madam', 'hon',
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
    'september', 'october', 'november', 'december',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    'group', 'company', 'year', 'day', 'week', 'month', 'world', 'us', 'uk', 'eu',
    'time', 'service', 'minister', 'government', 'new', 'old', 'get', 'like'
}