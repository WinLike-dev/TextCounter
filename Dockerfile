# Dockerfile

# Python 3.10-slim 이미지를 기반으로 사용 (가볍고 효율적)
FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리를 /usr/src/app으로 설정
WORKDIR /usr/src/app

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# TextBlob이 필요로 하는 NLTK 데이터를 다운로드합니다.
# 이 과정이 없으면 TextBlob 사용 시 오류가 발생할 수 있습니다.
RUN python -m textblob.download_corpora lite

# 프로젝트의 모든 파일(Django 코드, data_processor 등)을 작업 디렉토리로 복사
COPY . .
COPY entrypoint.sh /usr/src/app/
RUN chmod +x /usr/src/app/entrypoint.sh
# 6. 포트 노출 (선택 사항이지만 명시해둡니다)
EXPOSE 8000

# Django 서버의 기본 실행 명령어를 정의합니다. (docker-compose에서 오버라이드됨)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]