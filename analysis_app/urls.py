# analysis_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # 워커에게 분산 처리 명령을 내리는 엔드포인트
    path('start_distributed_rebuild/', views.start_distributed_rebuild_view, name='start_distributed_rebuild'),
    # 마스터에서 DB를 초기화하는 엔드포인트
    path('reset_all_db/', views.reset_all_db_view, name='reset_all_db'),
    # 조건부 워드클라우드 생성 엔드포인트
    path('wordcloud/', views.wordcloud_view, name='wordcloud_view'),
]