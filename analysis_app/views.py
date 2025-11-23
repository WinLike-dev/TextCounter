# analysis_app/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from wordcloud import WordCloud
import io
import base64
from typing import List, Tuple, Optional, Dict, Any
from data_processor.cache_manager import get_top_nouns_for_conditions
from data_processor.importer import run_extraction_and_save_to_category_nouns
from data_processor.constants import TOP_N


def generate_word_cloud_image(word_counts: List[Dict[str, int]]) -> Optional[str]:
    """WordCloud 이미지를 생성하고 base64 문자열로 반환합니다. (dict 형식에 맞게 수정)"""
    word_freq_dict = {item['word']: item['count'] for item in word_counts}
    if not word_freq_dict: return None

    # 💡 [수정] 폰트 경로를 사용하지 않고 WordCloud를 생성하여 OSError 방지
    # 폰트 경로를 찾지 못하여 'OSError: cannot open resource'가 발생했습니다.
    # 해당 부분을 제거하여 WordCloud가 시스템 기본 폰트를 사용하도록 합니다.
    # try:
    #     font_path = 'static/malgun.ttf'
    #     wc = WordCloud(
    #         background_color="white",
    #         width=800, height=400, max_words=len(word_freq_dict),
    #         font_path=font_path
    #     )
    # except ValueError:
    #     # 폰트가 없을 경우 기본 폰트 사용
    #     wc = WordCloud(
    #         background_color="white",
    #         width=800, height=400, max_words=len(word_freq_dict)
    #     )

    # 폰트 설정 없이 WordCloud 객체 생성
    wc = WordCloud(
        background_color="white",
        width=800, height=400, max_words=len(word_freq_dict)
    )

    wc.generate_from_frequencies(word_freq_dict)

    img_io = io.BytesIO()
    wc.to_image().save(img_io, format='PNG')
    img_io.seek(0)

    return 'data:image/png;base64,' + base64.b64encode(img_io.read()).decode()


def index(request):
    """메인 페이지 뷰"""
    success_message = request.session.pop('success_message', None)
    return render(request, 'analysis_app/index.html', {'success_message': success_message, 'TOP_N': TOP_N})


def rebuild_imfiles_view(request):
    """DB 데이터 재생성 요청 처리 뷰"""
    if request.method == 'POST':
        try:
            run_extraction_and_save_to_category_nouns()
            request.session['success_message'] = "✅ ImFiles 데이터(file_noun_records) 재생성 완료!"
        except Exception as e:
            return render(request, 'analysis_app/error.html', {
                'message': f'데이터 재생성 중 오류 발생: {e}'
            }, status=500)

    return redirect(reverse('index'))


def wordcloud_view(request):
    """
    WordCloud 표시 뷰: GET 쿼리 매개변수를 받아 조건부 워드클라우드를 생성합니다.
    """

    # 1. 쿼리 매개변수 추출
    title = request.GET.get('title')
    tags_input = request.GET.get('tags')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    top_n = request.GET.get('top_n', TOP_N)

    try:
        top_n = int(top_n)
    except ValueError:
        top_n = TOP_N

    # tags_input을 쉼표로 분리하고 공백을 제거하여 리스트로 만듦
    parsed_tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else None

    # 2. 쿼리 객체(딕셔너리) 구성
    query_conditions: Dict[str, Any] = {
        'title': title,
        'tags': parsed_tags,
        'start_date': start_date,
        'end_date': end_date,
    }

    # 💡 [이전 요청에 따라 제거됨] 유효성 검사 로직 삭제: 조건이 없어도 전체 분석을 위해 진행합니다.
    # if not (title or parsed_tags or start_date or end_date):
    #     return render(request, 'analysis_app/error.html', {
    #         'message': 'Title, Tags, Start Date, End Date 중 최소한 하나는 입력해야 합니다.'
    #     }, status=400)

    # 3. cache_manager를 통해 조건부 명사 데이터 가져오기 (객체 전달)
    top_words_data = get_top_nouns_for_conditions(
        query_conditions=query_conditions,
        top_n=top_n
    )

    if top_words_data is None:
        return render(request, 'analysis_app/error.html', {
            'message': '데이터를 처리하는 중 오류가 발생했습니다. 데이터베이스 연결을 확인하세요.'
        }, status=500)

    # 4. 데이터로 워드클라우드 이미지 생성
    image_base64 = generate_word_cloud_image(top_words_data)

    # 5. Context 구성 및 렌더링
    context = {
        # 조건을 템플릿에 전달하여 표시
        'title': title or '전체',
        'tags': ', '.join(parsed_tags) if parsed_tags else '전체',
        'start_date': start_date or '전체',
        'end_date': end_date or '전체',
        'top_n': top_n,

        'image_base64': image_base64,
        'top_words': top_words_data,
    }

    return render(request, 'analysis_app/wordcloud.html', context)