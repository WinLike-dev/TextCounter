# analysis_app/views.py

from django.shortcuts import render, redirect # redirect 추가
from wordcloud import WordCloud
import io
import base64
from typing import List, Tuple
from data_processor.cache_manager import get_top_words_and_manage_cache
from data_processor.importer import run_extraction_and_save_to_category_nouns # 🌟 새로 import
from data_processor.constants import TOP_N
from django.urls import reverse

CATEGORIES = ['business', 'entertainment', 'politics', 'sport', 'tech']


def generate_word_cloud_image(word_counts: List[Tuple[str, int]]) -> str:
    """WordCloud 이미지를 생성하고 base64 문자열로 반환합니다."""
    word_freq_dict = dict(word_counts)
    if not word_freq_dict: return ""

    wc = WordCloud(
        background_color="white",
        width=800, height=400, max_words=TOP_N
    )

    wc.generate_from_frequencies(word_freq_dict)
    img_byte_arr = io.BytesIO()
    wc.to_image().save(img_byte_arr, format='PNG')
    encoded_img = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

    return f"data:image/png;base64,{encoded_img}"


def index(request):
    """메인 페이지 뷰"""
    # 쿼리 파라미터에서 성공 메시지를 받아서 표시할 수 있도록 context에 추가
    success_message = request.GET.get('message')
    context = {
        'categories': CATEGORIES,
        'success_message': success_message # 🌟 메시지 추가
    }
    return render(request, 'analysis_app/index.html', context)


# 🌟 새로 추가된 뷰 함수
def rebuild_imfiles_view(request):
    """
    ImFiles(category_nouns) 재생성 로직을 실행합니다.
    웹 요청에서는 Command 객체를 사용하지 않고, 직접 함수를 호출합니다.
    """
    if request.method == 'POST':
        # 데이터 처리 함수 호출
        # NOTE: 이 작업은 시간이 오래 걸릴 수 있으므로 실제 서비스에서는 Celery 같은 비동기 큐를 사용해야 합니다.
        # 여기서는 간단히 동기적으로 처리합니다.
        run_extraction_and_save_to_category_nouns()

        # 성공 메시지와 함께 메인 페이지로 리다이렉트
        success_msg = "✅ ImFiles 데이터 (원본 명사 목록)가 성공적으로 재생성되었습니다. 캐시 데이터는 요청 시 업데이트됩니다."
        return redirect(f"{reverse('index')}?message={success_msg}")

    # POST 요청이 아니면 메인 페이지로 리다이렉트
    return redirect('index')

def wordcloud_view(request, category_name):
    """WordCloud 표시 뷰: OutputFiles를 통해 데이터를 가져옵니다."""
    category = category_name.lower()
    if category not in CATEGORIES:
        return render(request, 'analysis_app/error.html', {'message': f"알 수 없는 카테고리: {category_name}"}, status=404)

    # cache_manager를 통해 OutputFiles 데이터 가져오기
    top_words_data = get_top_words_and_manage_cache(category)

    if top_words_data:
        image_base64 = generate_word_cloud_image(top_words_data)
        context = {
            'category': category.upper(),
            'image_base64': image_base64,
            'top_words': top_words_data,
            'top_n': TOP_N
        }
        return render(request, 'analysis_app/wordcloud.html', context)
    else:
        return render(request, 'analysis_app/error.html',
                      {'message': f"{category.upper()} 카테고리의 데이터를 찾거나 처리할 수 없습니다. 'make_imfiles' 명령을 먼저 실행했는지 확인하세요."},
                      status=500)