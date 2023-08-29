import csv

from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

FILE_TABLES = {
    'ingredients': Ingredient,
    'tags': Tag,
    'recipes': Recipe,
    'recipeingredients': RecipeIngredient
}


class Command(BaseCommand):
    help = 'load data from csv'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str, help='filename')

    def handle(self, *args, **kwargs):
        filename = kwargs['filename']
        if filename not in FILE_TABLES:
            self.stdout.write(self.style.ERROR(
                f'***** Unknown file: "{filename}.csv"'))
        else:
            with open(f'../data/{filename}.csv', encoding='utf-8') as csv_file:
                csv_reader = csv.DictReader(csv_file, delimiter=',')
                FILE_TABLES[filename].objects.bulk_create(
                    FILE_TABLES[filename](**data) for data in csv_reader)
                self.stdout.write(self.style.SUCCESS(
                    f'***** Imported: {csv_reader.line_num-1} lines'))
