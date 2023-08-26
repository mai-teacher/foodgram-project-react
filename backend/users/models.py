# import enum

from django.contrib.auth import get_user_model
from django.db import models

# Ограничения полей
EMAIL_LIMIT = 254
FIRST_NAME_LIMIT = 150
LAST_NAME_LIMIT = 150
PASSWORD_LIMIT = 150
USERNAME_LIMIT = 150


User = get_user_model()


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
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(fields=['author', 'user'],
                                    name='unique_follow'),
            models.CheckConstraint(name='prevent_self_follow',
                                   check=~models.Q(user=models.F('author')))
        ]

    def __str__(self) -> str:
        # return f'{self.user.username} -> {self.author.username}'
        return f'{self.user} -> {self.author}'
