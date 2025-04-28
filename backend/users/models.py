# users/models.py

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class User(AbstractUser):
    """Custom User model for Foodgram project."""

    MAX_EMAIL_LENGTH = 254
    MAX_USERNAME_LENGTH = 150
    MAX_NAME_LENGTH = 150

    email = models.EmailField(
        'Email',
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
    )
    username = models.CharField(
        'Username',
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator()],
    )
    first_name = models.CharField(
        'First name',
        max_length=MAX_NAME_LENGTH,
    )
    last_name = models.CharField(
        'Last name',
        max_length=MAX_NAME_LENGTH,
    )
    avatar = models.ImageField(
        'Avatar',
        upload_to='users/',
        null=True,
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['id']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Model for user subscriptions."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Subscriber',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Author',
    )

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} follows {self.author}'
