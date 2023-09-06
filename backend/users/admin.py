from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from users.models import Subscription, User

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email',
        'first_name', 'last_name',
        'get_recipe_count', 'get_following')
    list_filter = ('email', 'username')
    readonly_fields = ('get_following', 'get_recipe_count')

    @admin.display(description='Рецептов')
    def get_recipe_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Подписчиков')
    def get_following(self, obj):
        return obj.following.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user', 'author')
