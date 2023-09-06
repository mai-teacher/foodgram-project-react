from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from foodgram_backend.constants import (
    MAX_AMOUNT,
    MAX_COOKING_TIME,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


class FoodgramUserSerializer(serializers.ModelSerializer):
    """Сериализатор объектов типа User. Просмотр пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        read_only_fields = ('is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and not request.user.is_anonymous
                and request.user.follower.filter(author=obj.id).exists())


class SubscriptionSerializer(FoodgramUserSerializer):
    """Сериализатор объектов типа Subscription. Подписки."""

    recipes = serializers.SerializerMethodField()
    # recipes_count = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='author__recipes.count')

    class Meta:
        # model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = ('is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Получение рецептов автора."""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = obj.author.recipes.all()
        if limit:
            queryset = queryset[:int(limit)]
        return ShortRecipeSerializer(queryset, many=True).data

    # def get_recipes_count(self, obj):
    #     """Получение количества рецептов автора."""
    #     return obj.author.recipes.all().count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and not request.user.is_anonymous
                and request.user.follower.filter(author=obj.id).exists())


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор объектов типа Tag. Список тегов."""

    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор объектов типа Ingredient. Список ингредиентов."""

    class Meta:
        fields = '__all__'
        model = Ingredient


class WriteRecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор объектов типа RecipeIngredient на запись."""

    id = serializers.IntegerField()
    # id = serializers.PrimaryKeyRelatedField(
    # source=?, queryset=RecipeIngredient.objects.all())
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(
                MIN_AMOUNT, message='В рецепте должны быть ингредиенты'),
            MaxValueValidator(
                MAX_AMOUNT, message='Слишком большое количество')])

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор (краткий) объектов типа Recipe."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор объектов типа Recipe. Чтение рецептов."""

    tags = TagSerializer(many=True)
    author = FoodgramUserSerializer()
    image = serializers.ReadOnlyField(source='image.url')
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_ingredients(self, obj):
        """Получение ингредиентов."""
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipe_ingredients__amount'))

    def get_is_favorited(self, data):
        request = self.context.get('request')
        return (request and not request.user.is_anonymous
                and request.user.favorites.filter(recipe=data).exists())

    def get_is_in_shopping_cart(self, data):
        request = self.context.get('request')
        return (request and not request.user.is_anonymous
                and request.user.shoppingcarts.filter(recipe=data).exists())


class RecipeWriteSerializer(
        serializers.ModelSerializer):
    """Сериализация объектов типа Recipes. Запись рецептов."""

    author = FoodgramUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    ingredients = WriteRecipeIngredientSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message='Время приготовления должно быть больше 1 минуты.'),
            MaxValueValidator(
                MAX_COOKING_TIME, message='Слишком большое время готовки')])

    class Meta:
        model = Recipe
        exclude = ('pub_date',)
        read_only_fields = ('author',)

    def validate_image(self, value):
        """Валидация картинки при заполнении рецепта."""
        if not value:
            raise serializers.ValidationError(
                'Ошибка: отсутствует картинка.')

    def validate_tags(self, value):
        """Валидация тегов при заполнении рецепта."""
        if not value:
            raise serializers.ValidationError(
                'Ошибка: минимально должен быть 1 тег.')
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Ошибка: тег не должен повторяться.')
        return value

    def validate_ingredients(self, value):
        """Валидация ингредиентов при заполнении рецепта."""
        if not value:
            raise serializers.ValidationError(
                'Ошибка: минимально должен быть 1 ингредиент.')
        ingredients = [item['id'] for item in value]
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'Ошибка: ингредиент не должен повторяться.')
        return value

    @staticmethod
    def add_ingredients_and_tags(instance, ingredients, tags):
        """Добавление ингредиентов и тегов."""
        instance.tags.set(tags)
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=instance,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount'],
            ) for ingredient in ingredients])

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context.get('request').user, **validated_data)
        self.add_ingredients_and_tags(recipe, ingredients, tags)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        instance.ingredients.clear()
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = self.add_ingredients_and_tags(instance, ingredients, tags)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeReadSerializer(
            instance=instance, context=self.context)
        return serializer.data


class BaseUserRecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор объектов типа Favorite/ShoppingCart."""

    class Meta:
        abstract = True

    def validate(self, data):
        request = self.context['request']
        user = request.user
        is_exist = self.Meta.model.objects.filter(
            user=user, recipe=data['recipe']).exists()

        if request.method == 'POST' and is_exist:
            raise serializers.ValidationError(
                'Ошибка: этот рецепт уже добавлен.')
        if request.method == 'DELETE' and not is_exist:
            raise serializers.ValidationError(
                'Ошибка: этот рецепт отсутствует.')
        return data


class FavoriteSerializer(BaseUserRecipeSerializer):
    """Сериализатор объектов типа Favorite. Проверка избранного."""

    class Meta:
        model = Favorite
        fields = '__all__'


class ShoppingCartSerializer(BaseUserRecipeSerializer):
    """Сериализатор объектов типа ShoppingCart. Проверка списка покупок."""

    class Meta:
        model = ShoppingCart
        fields = '__all__'

# class FavoriteSerializer(serializers.ModelSerializer):
#     """Сериализатор объектов типа Favorite. Проверка избранного."""

#     class Meta:
#         model = Favorite
#         fields = ('user', 'recipe')

#     def validate(self, data):
#         request = self.context['request']
#         user = request.user
#         is_exist = user.favorites.filter(recipe=data['recipe']).exists()

#         if request.method == 'POST' and is_exist:
#             raise serializers.ValidationError(
#                 'Ошибка: этот рецепт уже добавлен в избранном')
#         if request.method == 'DELETE' and not is_exist:
#             raise serializers.ValidationError(
#                 'Ошибка: этот рецепт отсутствует в избранном')
#         return data


# class ShoppingCartSerializer(serializers.ModelSerializer):
#     """Сериализатор объектов типа ShoppingCart. Проверка списка покупок."""

#     class Meta:
#         model = ShoppingCart
#         fields = ('user', 'recipe')

#     def validate(self, data):
#         request = self.context['request']
#         user = request.user
#         recipe = data['recipe']
#         is_cart = user.shoppingcarts.filter(recipe=recipe).exists()

#         if request.method == 'POST' and is_cart:
#             raise serializers.ValidationError(
#                 'Ошибка: этот рецепт уже добавлен в список покупок')
#         if request.method == 'DELETE' and not is_cart:
#             raise serializers.ValidationError(
#                 'Ошибка: этот рецепт отсутствует в списке покупок')
#         return data


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор объектов типа Subscription. Проверка подписки."""
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        user = data['user']
        author = data['author']
        subscribed = user.follower.filter(author=author).exists()

        if self.context.get('request').method == 'POST':
            if user == author:
                raise serializers.ValidationError(
                    'Ошибка: подписка на себя не разрешена')
            if subscribed:
                raise serializers.ValidationError('Ошибка: вы уже подписаны')
        if self.context.get('request').method == 'DELETE':
            if user == author:
                raise serializers.ValidationError(
                    'Ошибка: отписка от самого себя не разрешена')
            if not subscribed:
                raise serializers.ValidationError(
                    'Ошибка: вы не подписаны')
        return data
