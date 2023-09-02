from django.db.models import F
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from users.models import Subscription, User


class FoodgramUserCreateSerializer(UserCreateSerializer):
    """Сериализатор объектов типа User. Создание пользователя."""

    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())])
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())])
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class GetIsSubscribedMixin:
    """Миксин отображения подписки на пользователя"""

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.follower.filter(author=obj.id).exists()


class GetFavoriteShoppingCartMixin:
    """Миксин отображения в избранном и списке покупок."""

    def get_is_favorited(self, data):
        user = self.context['request'].user
        return user.favorites.filter(recipe=data).exists()

    def get_is_in_shopping_cart(self, data):
        user = self.context['request'].user
        return user.shopping_cart.filter(recipe=data).exists()


class GetIngredientsMixin:
    """Миксин для рецептов."""

    def get_ingredients(self, obj):
        """Получение ингредиентов."""
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipe_ingredients__amount')
        )


class FoodgramUserSerializer(GetIsSubscribedMixin, UserSerializer):
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


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор (краткий) объектов типа Recipe."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class RecipeReadSerializer(
        GetIngredientsMixin,
        GetFavoriteShoppingCartMixin,
        serializers.ModelSerializer):
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


class RecipeWriteSerializer(
        GetIngredientsMixin,
        GetFavoriteShoppingCartMixin,
        serializers.ModelSerializer):
    """Сериализация объектов типа Recipes. Запись рецептов."""

    author = FoodgramUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)
        read_only_fields = ('author',)

    def validate(self, data):
        """Валидация ингредиентов при заполнении рецепта."""
        ingredients = []
        if not self.initial_data['ingredients']:
            raise serializers.ValidationError(
                'Ошибка: минимально должен быть 1 ингредиент.')
        for item in self.initial_data['ingredients']:
            ingredient = get_object_or_404(Ingredient, id=item['id'])
            if ingredient in ingredients:
                raise serializers.ValidationError(
                    'Ошибка: ингредиент не должен повторяться.')
            if int(item['amount']) < 1:
                raise serializers.ValidationError(
                    'Ошибка: количество ингредиента должно быть больше 0')
            ingredients.append(ingredient)
            data['ingredients'] = self.initial_data['ingredients']
        return data

    def validate_cooking_time(self, time):
        """Валидация времени приготовления."""
        if int(time) < 1:
            raise serializers.ValidationError(
                'Ошибка: время приготовления должно быть больше 0')
        return time

    def add_ingredients_and_tags(self, instance, ingredients, tags):
        """Добавление ингредиентов и тегов."""
        for tag in tags:
            instance.tags.add(tag)

        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=instance,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount'],
            ) for ingredient in ingredients])
        return instance

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        return self.add_ingredients_and_tags(
            recipe, ingredients=ingredients, tags=tags)

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance = self.add_ingredients_and_tags(
            instance, ingredients=ingredients, tags=tags)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeReadSerializer(
            instance=instance, context={'request': self.context['request']})
        return serializer.data


class FavoriteSerializer(serializers.Serializer):
    """Сериализатор объектов типа Favorite. Проверка избранного."""

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        request = self.context['request']
        user = request.user
        recipe = data['recipe']
        favorite = user.favorites.filter(recipe=recipe).exists()

        if request.method == 'POST' and favorite:
            raise serializers.ValidationError(
                'Ошибка: этот рецепт уже добавлен в избранном')
        if request.method == 'DELETE' and not favorite:
            raise serializers.ValidationError(
                'Ошибка: этот рецепт отсутствует в избранном')
        return data


class ShoppingCartSerializer(serializers.Serializer):
    """Сериализатор объектов типа ShoppingCart. Проверка списка покупок."""

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        request = self.context['request']
        user = request.user
        recipe = data['recipe']
        is_cart = user.shopping_cart.filter(recipe=recipe).exists()

        if request.method == 'POST' and is_cart:
            raise serializers.ValidationError(
                'Ошибка: этот рецепт уже добавлен в список покупок')
        if request.method == 'DELETE' and not is_cart:
            raise serializers.ValidationError(
                'Ошибка: этот рецепт отсутствует в списке покупок')
        return data


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


class SubscriptionSerializer(
        GetIsSubscribedMixin, serializers.ModelSerializer):
    """Сериализатор объектов типа Subscription. Подписки."""

    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
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

    def get_recipes(self, obj):
        """Получение рецептов автора."""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = obj.author.recipes.all()
        if limit:
            queryset = queryset[:int(limit)]
        return ShortRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        """Получение количества рецептов автора."""
        return obj.author.recipes.all().count()
