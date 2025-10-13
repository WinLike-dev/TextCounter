# myapp/management/commands/make_imfiles.py

from django.core.management.base import BaseCommand
from data_processor.importer import run_extraction_and_save_to_category_nouns


class Command(BaseCommand):
    help = 'CSV에서 명사를 추출하여 category_nouns(ImFiles) 컬렉션에 저장합니다.'

    def handle(self, *args, **options):
        self.stdout.write("ImFiles 생성 작업 시작...")

        run_extraction_and_save_to_category_nouns()

        self.stdout.write(self.style.SUCCESS("ImFiles 생성 작업 완료."))