# data_processor/constants.py

import os

# ----------------------------------------------------------------------
# 1. MongoDB 연결 설정
# ----------------------------------------------------------------------
# MONGO_HOST: 워커가 DB에 접근할 때는 환경 변수를 통해 마스터/DB 서버의 Public IP를 받게 됩니다.
MONGO_HOST = os.environ.get('MONGO_HOST', 'db')
MONGO_PORT = os.environ.get('MONGO_PORT', '27017')
DB_NAME = os.environ.get('MONGO_DB', 'BBC_analysis_db')
MONGO_USER = os.environ.get('MONGO_USER', 'mongouser')
MONGO_PASS = os.environ.get('MONGO_PASS', '1234')

MONGO_URI = (
    f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{DB_NAME}"
    "?authSource=admin"
)

# ----------------------------------------------------------------------
# 2. 분산 워커 설정 (다중 파일 및 Public IP 기반 주소)
# ----------------------------------------------------------------------
RECORD_NOUNS_COLLECTION = "ImFiles"
TOP_NOUNS_CACHE_COLLECTION = "CacheDatas"
TOP_N = 50

# A. 🌟 워커 이름 및 할당된 파일 경로 목록 🌟
WORKER_CHUNK_FILES = {
    "Worker-1": [
        "data/2014.csv",
        "data/2015.csv",
        "data/2016.csv"
    ],
    "Worker-2": [
        "data/2017.csv",
        "data/2018.csv"
    ],
    "Worker-3": [
        "data/2019.csv",
        "data/2020.csv"
    ]
}

# B. 이 인스턴스(컨테이너)의 역할 및 파일 경로 동적 설정
WORKER_NAME = os.environ.get('WORKER_NAME', 'Master')
WORKER_FILE_PATH = WORKER_CHUNK_FILES.get(WORKER_NAME, None)
WORKER_SERVER = "3.26.14.106"

# C. 🌟 마스터가 사용할 워커 주소 목록 (Public IP 기반) 🌟
#    * 중요: 이 IP를 각 워커 디바이스의 실제 Public/Private IP로 대체해야 합니다.
#    * 49.168.187.55와 동일 대역의 임의의 Public IP를 가정합니다.
WORKER_ADDRESSES = [
    # 📌 IP 주소가 Worker-1, 2, 3의 실제 Public IP와 일치하는지 확인하세요.
    {"name": "Worker-1", "host": WORKER_SERVER, "port": 8001},
    {"name": "Worker-2", "host": WORKER_SERVER, "port": 8002},
    {"name": "Worker-3", "host": WORKER_SERVER, "port": 8003}
]


# ----------------------------------------------------------------------
# 3. MongoDB 문서 필드 스키마 정의
# ----------------------------------------------------------------------
DB_FIELD_HEADING = 'Heading'
DB_FIELD_DATE = 'Date'
DB_FIELD_TAGS = 'Tags'
DB_FIELD_ARTICLES = 'Articles'
DB_FIELD_NOUNS = 'nouns'
DB_FIELD_RECORD_ID = 'record_id'

CACHE_FIELD_TITLE_QUERY = 'Title'
CACHE_FIELD_START_DATE_QUERY = 'StartDate'
CACHE_FIELD_END_DATE_QUERY = 'EndDate'
CACHE_FIELD_TAGS_QUERY = 'Tags'
CACHE_FIELD_TOP_N = 'top_n'
CACHE_FIELD_TOP_WORDS = 'top_words'


# ----------------------------------------------------------------------
# 4. CSV 파일 구조 및 DB 매핑 설정
# ----------------------------------------------------------------------
CSV_COLUMNS_SOURCE = ['title', 'text', 'timestamp', 'tags']

DB_FIELD_MAPPING = {
    'title': DB_FIELD_HEADING,
    'text': DB_FIELD_ARTICLES,
    'timestamp': DB_FIELD_DATE,
    'tags': DB_FIELD_TAGS,
}

DB_FIELD_DEFAULTS = {
    DB_FIELD_TAGS: [],
}

# ----------------------------------------------------------------------
# 5. 고유 명사 추출 제외 목록
# ----------------------------------------------------------------------
EXCLUDE_NOUNS = {
    'mr', 'mrs', 'ms', 'dr', 'prof', 'lord', 'sir', 'madam', 'hon',
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
    'september', 'october', 'november', 'december',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    'group', 'company', 'year', 'day', 'week', 'month', 'world', 'us', 'uk', 'eu',
    'time', 'service', 'minister', 'government', 'new', 'old', 'get', 'like',
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
    'i', 'we', 'you', 'he', 'she', 'it', 'they', 'us', 'him', 'her', 'them'
}