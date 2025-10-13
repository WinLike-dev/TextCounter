## 실행

```
# 가상환경 생성  (파이썬 3.12 버전)
python -m venv venv

# 가상환경 실행 (유닉스)
source ./venv/Scripts/activate
(윈도우)
.\venv\Scripts\activate

# 필요 package 설치
pip install -r requirements.txt

# 이미지를 빌드하고 
장고와 몽고 DB 두 서비스를 백그라운드 실행
docker-compose up --build -d

# 컨테이너 문제없는 지 확인 
docker-compose ps

# IMFiles 생성 명령
docker exec -it django-news-app python manage.py make_imfiles

# 브라우져로 접속
http://127.0.0.1:8000/
or http://localhost:8000/

# 추가 : 컨테이너 종료 시 
docker-compose down -v

```

