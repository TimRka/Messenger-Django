from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя
    """
    #нынче обязателен
    email = models.EmailField(unique=True, verbose_name='Email')
    #необязателен
    phone_regex = RegexValidator(
        regex=r'^\+?7?\d{10}$',
        message="Телефон в формате: +7XXXXXXXXXX (10 цифр)"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Телефон'
    )
    #доп инфа
    birth_date = models.DateField(blank=True, null=True, verbose_name='Дата рождения')
    bio = models.TextField(blank=True, null=True, verbose_name='О себе')
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    last_online = models.DateTimeField(auto_now=True, verbose_name='Был в сети')

    PRIVACY_CHOICES = [
        ('everyone', 'Все пользователи'),
        ('members_only', 'Только участники чатов'),
        ('no_one', 'Никто (кроме администраторов)'),
    ]

    email_privacy = models.CharField(
        max_length=20,
        choices=PRIVACY_CHOICES,
        default='members_only',
        verbose_name='Кто видит email'
    )

    phone_privacy = models.CharField(
        max_length=20,
        choices=PRIVACY_CHOICES,
        default='members_only',
        verbose_name='Кто видит телефон'
    )

    # Поля для параметров входа
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def can_see_email(self, viewer):
        if viewer == self or viewer.is_superuser or viewer.is_staff:
            return True

        if self.email_privacy == 'everyone':
            return True
        elif self.email_privacy == 'members_only':
            from chat.models import ChatMember
            user_chats = ChatMember.objects.filter(user=viewer).values_list('chat_id', flat=True)
            return ChatMember.objects.filter(chat_id__in=user_chats, user=self).exists()
        else:
            return False

    def can_see_phone(self, viewer):
        if viewer == self or viewer.is_superuser or viewer.is_staff:
            return True

        if self.phone_privacy == 'everyone':
            return True
        elif self.phone_privacy == 'members_only':
            from chat.models import ChatMember
            user_chats = ChatMember.objects.filter(user=viewer).values_list('chat_id', flat=True)
            return ChatMember.objects.filter(chat_id__in=user_chats, user=self).exists()
        else:
            return False