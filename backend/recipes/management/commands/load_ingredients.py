import csv
from typing import Any

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'load ingredients from csv'

    def handle(self, *args: Any, **options: Any):
        with open('../data/ingredients.csv', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
        #     lines = 0
        #     for row in csv_reader:
        #         name = row['name']
        #         unit = row['measurement_unit']
        #         ingredient = Ingredient(name=name, measurement_unit=unit)
        #         ingredient.save()
        #         lines += 1
        # print(f'   imported: {lines} lines')
            Ingredient.objects.bulk_create(
                Ingredient(**data) for data in csv_reader)
            self.stdout.write(self.style.SUCCESS(
                f'***** imported: {csv_reader.line_num-1} lines'))
