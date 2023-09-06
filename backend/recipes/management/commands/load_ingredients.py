import csv
from typing import Any

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'load ingredients from csv'

    def handle(self, *args: Any, **options: Any):
        if Ingredient.objects.exists():
            self.stdout.write(self.style.WARNING('Данные уже загружены!'))
            return
        line_num = 0
        try:
            with open('./data/ingredients.csv', encoding='utf-8') as csv_file:
                reader = csv.reader(csv_file, delimiter=',')
                for row in reader:
                    obj, status = Ingredient.objects.get_or_create(
                        name=row[0],
                        measurement_unit=row[1])
                    line_num += int(status)

        except FileNotFoundError:
            raise Exception('Файл ingredients.csv не найден')
        self.stdout.write(self.style.SUCCESS(
            f'***** импортировано: {line_num} строк'))
