import csv
from typing import Any

from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag

FILE_TABLES = [
    ('ingredients', Ingredient),
    ('tags', Tag),
]


class Command(BaseCommand):
    help = 'load ingredients from csv'

    def handle(self, *args: Any, **options: Any):
        for filename, model in FILE_TABLES:
            line_num = 0
            try:
                with open(f'./data/{filename}.csv',
                          encoding='utf-8') as csv_file:
                    reader = csv.reader(csv_file, delimiter=',')
                    header = next(reader)
                    for row in reader:
                        data = {key: value for key, value in zip(header, row)}
                        obj, status = model.objects.get_or_create(**data)
                        line_num += int(status)

            except FileNotFoundError:
                raise Exception('Файл "{filename}.csv" не найден')
            self.stdout.write(self.style.SUCCESS(
                f'***** Импортировано в {filename}: {line_num} строк'))
