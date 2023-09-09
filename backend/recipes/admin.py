from django.contrib import admin
from django.utils.safestring import mark_safe

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


class RecipeIngredientInline(admin.StackedInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'author', 'get_ingredients', 'get_favorite_count', 'get_image')
    list_filter = ('author', 'name', 'tags')
    readonly_fields = ('get_ingredients', 'get_favorite_count', )
    inlines = [RecipeIngredientInline]

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        recipe_ingredients = RecipeIngredient.objects.filter(recipe__id=obj.id)
        result = [ingredient for ingredient in recipe_ingredients]
        return result

    @admin.display(description='В избранном')
    def get_favorite_count(self, obj):
        return obj.favorites.count()

    @admin.display(description='Картинка')
    def get_image(self, obj):
        if obj.image.url is not None:
            return mark_safe(
                f'<img src={obj.image.url} width="80" height="60">')
        else:
            return ''


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name', )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
