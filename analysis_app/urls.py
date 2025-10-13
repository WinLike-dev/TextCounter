# myapp/urls.py (수정)

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('rebuild_imfiles/', views.rebuild_imfiles_view, name='rebuild_imfiles'), # 🌟 새로 추가
    path('<str:category_name>/', views.wordcloud_view, name='wordcloud_view'),
]