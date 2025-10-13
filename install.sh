#!/bin/bash

# 1. requirements.txt의 패키지 설치
pip install -r requirements.txt

# 2. TextBlob corpora 다운로드
python -m textblob.download_corpora

echo "모든 패키지 및 TextBlob 데이터 설치 완료."