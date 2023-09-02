from django_filters.rest_framework import CharFilter, FilterSet, filters
from django_filters.widgets import BooleanWidget
from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    """Класс для фильтрации обьектов Ingredients."""

    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """Класс для фильтрации обьектов Recipe."""

    author = filters.AllValuesMultipleFilter(
        field_name='author__id', label='Автор'
    )
    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")
    # is_in_shopping_cart = filters.BooleanFilter(
    #     widget=BooleanWidget(), label='В списке покупок'
    # )
    # is_favorited = filters.BooleanFilter(
    #     widget=BooleanWidget(), label='В избранном'
    # )

    is_favorited = filters.NumberFilter(method='get_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_in_shopping_cart', 'is_favorited')

    def get_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
