from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models

from foodgram_backend.constants import (
    MAX_AMOUNT,
    MAX_COOKING_TIME,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
    RECIPE_FIELD_LIMIT,
    TAG_COLOR_LIMIT,
)
from users.models import User


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        max_length=RECIPE_FIELD_LIMIT,
        verbose_name='название',
        db_index=True
    )
    color = models.CharField(
        max_length=TAG_COLOR_LIMIT,
        verbose_name='цвет в HEX-коде',
        validators=[
            RegexValidator(
                '^#([a-fA-F0-9]{6})',
                message='Поле должно содержать HEX-код цвета.', )
        ],

    )
    slug = models.SlugField(
        max_length=RECIPE_FIELD_LIMIT,
        verbose_name='слаг',
        unique=True
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        max_length=RECIPE_FIELD_LIMIT,
        verbose_name='название',
    )
    measurement_unit = models.CharField(
        max_length=RECIPE_FIELD_LIMIT,
        verbose_name='единицы измерения',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'), name='unique_ingredient')
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='автор публикации рецепта'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='дата добавления',
    )
    name = models.CharField(
        max_length=RECIPE_FIELD_LIMIT,
        verbose_name='название',
        db_index=True,
        help_text='Введите наименование рецепта'
    )
    image = models.ImageField(
        upload_to='images/',
        verbose_name='картинка',
        help_text='Выберите файл с картинкой',
    )
    text = models.TextField(
        verbose_name='текстовое описание рецепта',
        help_text='Введите текстовое описание рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='список ингредиентов',
        help_text='Выберите ингредиенты',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='время приготовления, в минутах',
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message='Время приготовления должно быть больше 1 минуты.'),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message=('Время приготовления должно быть меньше '
                         f'{MAX_COOKING_TIME} минут(ы).'))
        ],
        help_text='Введите время приготовления блюда',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='список тегов',
        help_text='Выберите теги',
    )

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель количества ингредиента в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        default=MIN_AMOUNT,
        verbose_name='количество',
        validators=[
            MinValueValidator(
                MIN_AMOUNT, message='В рецепте должны быть ингредиенты'),
            MaxValueValidator(
                MAX_AMOUNT,
                message=f'Количество должно быть менее {MAX_AMOUNT}')
        ],
        help_text='Введите количество ингредиента'
    )

    class Meta:
        ordering = ('recipe', 'ingredient')
        verbose_name = 'ингредиент к рецепту'
        verbose_name_plural = 'ингредиенты к рецептам'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient')
        ]

    def __str__(self):
        return (f'{self.ingredient.name} {self.amount} '
                f'{self.ingredient.measurement_unit}')


class UserRecipeAbstractModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='рецепт'
    )

    class Meta:
        abstract = True
        ordering = ('user', )
        default_related_name = '%(class)ss'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_user_%(class)s')]

    def __str__(self):
        return f'{self.user.username} -> {self.recipe.name}'


class Favorite(UserRecipeAbstractModel):
    """Модель для избранных рецептов."""

    class Meta(UserRecipeAbstractModel.Meta):
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'


class ShoppingCart(UserRecipeAbstractModel):
    """Модель списка покупок."""

    class Meta(UserRecipeAbstractModel.Meta):
        verbose_name = 'список покупок'
        verbose_name_plural = 'списки покупок'
