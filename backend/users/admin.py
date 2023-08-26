from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Subscription


UserAdmin.list_display = ('username', 'email', 'first_name', 'last_name')
UserAdmin.list_filter = ('email', 'username')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user', 'author')
