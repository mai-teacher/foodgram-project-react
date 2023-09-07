from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    SAFE_METHODS,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import LimitPageNumberPagination
from api.permissions import IsAdminAuthorOrReadOnly
from api.serializers import (
    FavoriteSerializer,
    FoodgramUserSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    ShortRecipeSerializer,
    SubscribeSerializer,
    SubscriptionSerializer,
    TagSerializer,
)
from foodgram_backend.constants import FILE_NAME, TITLE_SHOP_CART
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для отображения моделей Recipe/Favorite/Shopping_cart."""
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'ingredients', 'tags')
    serializer_class = RecipeWriteSerializer
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @staticmethod
    def add_recipe(model, model_serializer, request, id):
        data = {'user': request.user.id, 'recipe': id}
        serializer = model_serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        model.objects.create(user=request.user, recipe_id=id)
        serializer = ShortRecipeSerializer(id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_recipe(model, model_serializer, request, id):
        data = {'user': request.user.id, 'recipe': id}
        serializer = model_serializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        model.objects.filter(user=request.user, recipe__id=id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['post'], permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        """Добавить в избранное."""
        return self.add_recipe(
            model=Favorite,
            model_serializer=FavoriteSerializer,
            request=request,
            id=pk
        )

    @favorite.mapping.delete
    def del_favorite(self, request, pk=None):
        """Удалить из избранного."""
        return self.delete_recipe(
            model=Favorite,
            model_serializer=FavoriteSerializer,
            request=request,
            id=pk
        )

    @action(
        detail=True, methods=['post'], permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        """Добавить в список покупок."""
        return self.add_recipe(
            model=ShoppingCart,
            model_serializer=ShoppingCartSerializer,
            request=request,
            id=pk
        )

    @shopping_cart.mapping.delete
    def del_shopping_cart(self, request, pk=None):
        """Удалить из списка покупок."""
        return self.delete_recipe(
            model=ShoppingCart,
            model_serializer=ShoppingCartSerializer,
            request=request,
            id=pk
        )

    @staticmethod
    def send_shopping_cart(ingredients):
        result = TITLE_SHOP_CART
        result += '\n'.join(
            f'{ingredient["ingredient__name"]}'
            f' ({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["total"]}'
            for ingredient in ingredients
        )
        return FileResponse(result, as_attachment=True, filename=FILE_NAME)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        ingredients = (RecipeIngredient.objects.filter(
            recipe__shoppingcarts__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .order_by('ingredient__name')
            .annotate(total=Sum('amount'))
        )
        return self.send_shopping_cart(ingredients)


class UserSubscriptionViewSet(UserViewSet):
    """Вьюсет для отображения моделей User/Subscription."""

    queryset = User.objects.all()
    serializer_class = FoodgramUserSerializer
    pagination_class = LimitPageNumberPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(
        detail=False, methods=['get'], url_path='me', url_name='me',
        permission_classes=(IsAuthenticated,))
    def me(self, request, id=None):
        """Возвращает текущему пользователю подробную информацию о себе."""
        user_me = request.user
        serializer = FoodgramUserSerializer(
            user_me, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True, methods=['post'], permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id=None):
        """Подписаться на автора."""
        user = request.user
        author = get_object_or_404(User, pk=id)
        data = {'user': user.id, 'author': author.id}
        serializer = SubscribeSerializer(data=data,
                                         context={'request': request})
        serializer.is_valid(raise_exception=True)
        Subscription.objects.create(user=user, author=author)
        serializer = SubscriptionSerializer(
            author, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def del_subscribe(self, request, id=None):
        """Отписаться от автора."""
        user = request.user
        author = get_object_or_404(User, pk=id)
        data = {'user': user.id, 'author': author.id}
        serializer = SubscribeSerializer(data=data,
                                         context={'request': request})
        serializer.is_valid(raise_exception=True)
        user.follower.filter(author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Подписки."""
        user = request.user
        followers = user.follower.all()
        authors = [item.author.id for item in followers]
        queryset = User.objects.filter(pk__in=authors)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
