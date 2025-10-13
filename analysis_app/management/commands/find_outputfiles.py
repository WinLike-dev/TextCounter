# myapp/management/commands/find_outputfiles.py

from django.core.management.base import BaseCommand, CommandError
from data_processor.cache_manager import get_top_words_and_manage_cache
from analysis_app.views import CATEGORIES


class Command(BaseCommand):
    help = '특정 카테고리(들)에 대해 output_files(웹 캐시)를 미리 생성하거나 강제로 업데이트합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            'categories',
            nargs='*',
            type=str,
            help='캐시를 생성할 카테고리 이름 (예: business sport)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='기존 캐시가 있어도 강제로 재생성합니다.'
        )

    def handle(self, *args, **options):
        input_categories = options['categories']
        force_reprocess = options['force']

        # 처리할 카테고리 결정
        categories_to_process = []
        valid_categories = [c.lower() for c in CATEGORIES]

        if input_categories:
            for cat in input_categories:
                if cat.lower() in valid_categories:
                    categories_to_process.append(cat.lower())
                else:
                    self.stdout.write(self.style.ERROR(f"유효하지 않은 카테고리입니다: {cat}"))

            if not categories_to_process:
                raise CommandError("유효한 카테고리 인자가 없습니다.")
        else:
            categories_to_process = CATEGORIES
            self.stdout.write("⚠️ 인자가 없어 모든 카테고리에 대해 캐시 작업을 시작합니다.")

        self.stdout.write("\nOutputFiles 캐시 생성/업데이트 시작...")

        for category in categories_to_process:
            self.stdout.write(f" - [{category.upper()}] 캐시 처리 중 (Force: {force_reprocess})...")

            result = get_top_words_and_manage_cache(category, force_reprocess=force_reprocess)

            if result:
                action = "재생성" if force_reprocess else ("확인/생성" if len(result) > 0 else "데이터 없음")
                self.stdout.write(self.style.SUCCESS(f" - [{category.upper()}] 캐시 {action} 완료. ({len(result)}개 단어)"))
            else:
                self.stdout.write(self.style.WARNING(f" - [{category.upper()}] 데이터 처리 실패. ImFiles 생성을 먼저 확인하세요."))

        self.stdout.write(self.style.SUCCESS("\nOutputFiles 캐시 관리 작업 완료."))