from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from djoser.views import UserViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAdminAuthorOrReadOnly, IsAdminOrReadOnly
from api.serializers import (
    IngredientSerializer, FavoriteSerializer, RecipeReadSerializer,
    RecipeWriteSerializer, SubscribeSerializer, SubscriptionSerializer,
    ShoppingCartSerializer, ShortRecipeSerializer, TagSerializer)
from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag, Favorite)
from users.models import Subscription, User

FILE_NAME = "shopping-cart.txt"
TITLE_SHOP_CART = "Список покупок с сайта Foodgram:\n\n"


class ListRetrieveViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
    permission_classes = (IsAdminOrReadOnly,)


class TagViewSet(ListRetrieveViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ListRetrieveViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all()
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def add_recipe(self, model, model_serializer, request, pk):
        data = {'user': request.user.id, 'recipe': pk}
        serializer = model_serializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, id=pk)
            model.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        model.objects.filter(user=request.user, recipe__id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        """Добавить в избранное/Удалить из избранного."""
        return self.add_recipe(
            model=Favorite,
            model_serializer=FavoriteSerializer,
            request=request,
            pk=pk
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        """Добавить в список покупок/Удалить из списка покупок."""
        return self.add_recipe(
            model=ShoppingCart,
            model_serializer=ShoppingCartSerializer,
            request=request,
            pk=pk
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        ingredients = (RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .order_by('ingredient__name')
            .annotate(total=Sum("amount"))
        )
        result = TITLE_SHOP_CART
        result += '\n'.join(
                f'{ingredient["ingredient__name"]}'
                f' ({ingredient["ingredient__measurement_unit"]})'
                f' - {ingredient["total"]}'
                for ingredient in ingredients
        )
        print(result)
        response = HttpResponse(result, content_type='text/plain')
        response['Content-Disposition'] = f"attachment; filename={FILE_NAME}"
        return response


class SubscriptionViewSet(UserViewSet):
    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        """Подписаться на автора/отписаться от автора."""
        user = request.user
        author = get_object_or_404(User, pk=id)
        data = {'user': user.id, 'author': author.id}
        serializer = SubscribeSerializer(data=data,
                                         context={'request': request})
        serializer.is_valid(raise_exception=True)
        if request.method == 'POST':
            result = Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(
                result, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        user.follower.filter(author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Подписки."""
        user = request.user
        queryset = user.follower.all()
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)
