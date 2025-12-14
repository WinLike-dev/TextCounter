#!/bin/sh

# MongoDB 호스트와 포트 (docker-compose.yml의 db 서비스 이름)
HOST="db"
PORT="27017"

echo "Waiting for MongoDB to start on ${HOST}:${PORT}..."

# Telnet을 사용하여 MongoDB 포트가 열릴 때까지 무한정 대기
while ! nc -z ${HOST} ${PORT}; do
  sleep 0.1
done

echo "MongoDB started."

# 1. Django 마이그레이션 실행 (사라진 시스템 테이블 재생성)
echo "Running Django migrations..."
python manage.py migrate --noinput

# 2. Django 서버 시작
exec "$@"