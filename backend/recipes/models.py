from django.core.validators import MinValueValidator
from django.db import models
from users.models import User

# Ограничения полей
INGREDIENT_NAME_LIMIT = 200
MEASUREMENT_UNIT_LIMIT = 200

RECIPE_NAME_LIMIT = 200

TAG_COLOR_LIMIT = 7
TAG_NAME_LIMIT = 200
TAG_SLUG_LIMIT = 200

# Ограничения валидации
MIN_COOKING_TIME = 1


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        max_length=TAG_NAME_LIMIT,
        verbose_name='название',
        db_index=True
    )
    color = models.CharField(
        max_length=TAG_COLOR_LIMIT,
        verbose_name='цвет в HEX-коде',
    )
    slug = models.SlugField(
        max_length=TAG_SLUG_LIMIT,
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
        max_length=INGREDIENT_NAME_LIMIT,
        verbose_name='название',
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_LIMIT,
        verbose_name='единицы измерения',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'

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
        max_length=RECIPE_NAME_LIMIT,
        verbose_name='название',
        db_index=True,
        help_text='Введите наименование рецепта'
    )
    image = models.ImageField(
        null=True,
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
        validators=[MinValueValidator(
            1, message='Время приготовления должно быть больше 1 минуты.')],
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
    amount = models.IntegerField(
        verbose_name='количество'
    )

    class Meta:
        ordering = ('recipe', 'ingredient')
        verbose_name = 'ингредиент к рецепту'
        verbose_name_plural = 'ингредиенты к рецептам'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'), name='unique_ingredient'
            )
        ]

    def __str__(self):
        return (f'{self.recipe.name}: {self.ingredient.name}-{self.amount} '
                f'{self.ingredient.measurement_unit}')


class Favorite(models.Model):
    """Модель для избранных рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='рецепт'
    )

    class Meta:
        ordering = ('-id', )
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_user_recipe')]

    def __str__(self):
        return f'{self.user.username} -> {self.recipe.name}'


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='рецепт'
    )

    class Meta:
        ordering = ('-id', )
        verbose_name = 'список покупок'
        verbose_name_plural = 'списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_user_cart')]

    def __str__(self):
        return f'{self.user.username} -> {self.recipe.name}'
