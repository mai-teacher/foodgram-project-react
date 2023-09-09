from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from foodgram_backend.constants import EMAIL_LIMIT, USER_FIELD_LIMIT


class User(AbstractUser):
    username = models.CharField(
        unique=True,
        max_length=USER_FIELD_LIMIT,
        validators=[
            RegexValidator(
                regex='me',
                inverse_match=True,
                message='Пользователя нельзя называть "me".', )],
        verbose_name='уникальное имя',
        help_text='Введите уникальное имя пользователя')
    email = models.EmailField(
        unique=True,
        max_length=EMAIL_LIMIT,
        verbose_name='электронная почта',
        help_text='Введите электронную почту пользователя')
    first_name = models.CharField(
        max_length=USER_FIELD_LIMIT,
        verbose_name='имя',
        help_text='Введите имя пользователя')
    last_name = models.CharField(
        max_length=USER_FIELD_LIMIT,
        verbose_name='фамилия',
        help_text='Введите фамилию пользователя')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('username', )
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='подписан на'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        ordering = ('user', 'author')
        constraints = [
            models.UniqueConstraint(fields=['author', 'user'],
                                    name='unique_follow'),
            models.CheckConstraint(name='prevent_self_follow',
                                   check=~models.Q(user=models.F('author')))
        ]

    def __str__(self) -> str:
        return f'{self.user} -> {self.author}'
