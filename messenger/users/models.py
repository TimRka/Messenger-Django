from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import date
from django.conf import settings

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
        unique=True,
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

    def clean(self):
        super().clean()
        # 1
        if self.email:
            if '@' not in self.email or '.' not in self.email.split('@')[-1]:
                raise ValidationError({'email': 'Введите корректный email адрес.'})
        # 2
        if self.phone:
            import re
            digits = re.sub(r'\D', '', self.phone)
            if len(digits) == 10:
                normalized = f'+7{digits}'
            elif len(digits) == 11 and digits.startswith('7'):
                normalized = f'+{digits}'
            elif len(digits) == 11 and digits.startswith('8'):
                normalized = f'+7{digits[1:]}'
            else:
                raise ValidationError({'phone': 'Неверный формат телефона. Используйте +7XXXXXXXXXX'})
            self.phone = normalized
        # 3
        if self.birth_date and self.birth_date > date.today():
            raise ValidationError({'birth_date': 'Дата рождения не может быть в будущем.'})
        # 4
        if self.bio and len(self.bio) > 300:
            raise ValidationError({'bio': 'Bio не может быть длиннее 300 символов.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)




class UserPreferences(models.Model):
    THEME_CHOICES = [
        ('light', 'Светлая'),
        ('dark', 'Тёмная'),
        ('high_contrast', 'Высокий контраст'),
        ('sepia', 'Сепия (для глаз)'),
    ]

    FONT_CHOICES = [
        ('system', 'Системный'),
        ('sans-serif', 'Без засечек (Arial)'),
        ('serif', 'С засечками (Georgia)'),
        ('roboto', 'Roboto'),
        ('inter', 'Inter'),
        ('monospace', 'Моноширинный'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preferences'
    )

    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='light')
    font_family = models.CharField(max_length=20, choices=FONT_CHOICES, default='system')
    font_size = models.IntegerField(default=16, help_text="14–22 px")

    class Meta:
        verbose_name = "Настройки пользователя"
        verbose_name_plural = "Настройки пользователей"

    def __str__(self):
        return f"Настройки {self.user}"
