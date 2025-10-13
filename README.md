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

# migrate 명령어로 DB 생성
python manage.py makemigrations
python manage.py migrate

# 서버 실행
python manage.py runserver

# 브라우져로 접속
http://127.0.0.1:8000/main/
```
