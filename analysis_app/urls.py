# myapp/urls.py (수정됨)

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('rebuild_imfiles/', views.rebuild_imfiles_view, name='rebuild_imfiles'),
    # 조건부 검색을 위해 매개변수 없이 /wordcloud/ 경로로 변경
    path('wordcloud/', views.wordcloud_view, name='wordcloud_view'),
]