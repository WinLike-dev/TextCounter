# myapp/management/commands/find_outputfiles.py

from django.core.management.base import BaseCommand, CommandError
from data_processor.cache_manager import get_top_nouns_for_conditions
from data_processor.constants import TOP_N
from typing import Dict, Any


class Command(BaseCommand):
    help = '특정 조건(Title, Tags, Date Range)에 대해 OutputFiles 캐시를 미리 생성하거나 강제로 업데이트합니다.'

    def add_arguments(self, parser):

        parser.add_argument(
            '--title',
            type=str,
            default=None,
            help='캐시를 생성할 Heading (Title)의 부분 일치 문자열 (예: Apple)'
        )
        parser.add_argument(
            '--tags',
            type=str,
            default=None,
            help='캐시를 생성할 Tags (예: Culture,Life - 쉼표로 구분)'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            default=None,
            help='캐시를 생성할 날짜 범위의 시작일 (예: 2024-01-01)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            default=None,
            help='캐시를 생성할 날짜 범위의 종료일 (예: 2024-12-31)'
        )
        parser.add_argument(
            '--top-n',
            type=int,
            default=TOP_N,
            help=f'추출할 상위 단어 개수 (기본값: {TOP_N})'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='기존 캐시가 있어도 강제로 재생성합니다. (cache_manager 함수가 이를 지원해야 함)'
        )

    def handle(self, *args, **options):
        title = options['title']
        tags_input = options['tags']
        start_date = options['start_date']
        end_date = options['end_date']
        top_n = options['top_n']
        force_reprocess = options['force']

        # tags_input을 쉼표로 분리하고 공백을 제거하여 리스트로 만듦
        parsed_tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else None

        # 쿼리 객체(딕셔너리) 구성
        query_conditions: Dict[str, Any] = {
            'title': title,
            'tags': parsed_tags,
            'start_date': start_date,
            'end_date': end_date,
        }

        # 💡 [수정] 최소 하나 이상의 조건 확인 로직 삭제: 조건이 없어도 전체 분석을 위해 진행합니다.
        # if not (title or parsed_tags or start_date or end_date):
        #     raise CommandError("Title, Tags, Start Date, End Date 중 최소한 하나는 인자로 제공해야 합니다.")

        self.stdout.write("\nOutputFiles 캐시 생성/업데이트 시작...")

        tags_log = ", ".join(parsed_tags) if parsed_tags else '전체'
        self.stdout.write(
            f" - [Title: {title or '전체'}, Tags: {tags_log}, Date Range: {start_date or '전체'} ~ {end_date or '전체'}] 캐시 처리 중 (Top N: {top_n}, Force: {force_reprocess})...")

        # 쿼리 객체 전달
        result = get_top_nouns_for_conditions(
            query_conditions=query_conditions,
            top_n=top_n
        )

        if result is None:
            self.stdout.write(self.style.ERROR(" - 오류 발생: 데이터 처리 중 문제가 발생했습니다. (DB 연결 등)"))
        elif result:
            self.stdout.write(self.style.SUCCESS(f" - ✅ 조건부 캐시 생성/확인 완료. 상위 {len(result)}개 단어 저장됨."))
        else:
            self.stdout.write(self.style.WARNING(" - ⚠️ 경고: 조건에 맞는 레코드가 없거나 추출된 명사가 없습니다."))