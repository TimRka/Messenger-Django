from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet


class Chat(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Chat {self.id}"

class ChatMember(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('admin', 'Admin'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')

    class Meta:
        unique_together = [['user', 'chat']]

    def __str__(self):
        return f"{self.user.username} in {self.chat.name} as {self.role}"

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    _text = models.TextField(db_column='text')
    created_at = models.DateTimeField(auto_now_add=True)
    _plain_text = ''
    @property
    def text(self):
        """Дешифровка при чтении"""
        if not self._text:
            return ''
        f = Fernet(settings.ENCRYPTION_KEY)
        return f.decrypt(self._text.encode()).decode()

    @text.setter
    def text(self, value):
        """Шифровка при сохранении"""
        if value:
            f = Fernet(settings.ENCRYPTION_KEY)
            self._text = f.encrypt(value.encode()).decode()
        else:
            self._text = ''
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username}: {self.text[:20]}"

    def clean(self):

        if hasattr(self, '_plain_text') and self._plain_text:
            plain_text = self._plain_text
        else:
            plain_text = self.text
        if not plain_text:
            raise ValidationError('Сообщение не может быть пустым.')
        if len(plain_text) > 2000:
            raise ValidationError('Сообщение не может быть длиннее 2000 символов.')
        if len(plain_text) < 1:
            raise ValidationError('Сообщение должно содержать хотя бы 1 символ.')

        # ЦЕНЗУРА
        forbidden = ['дурак', 'редиска', '67']
        lower_text = plain_text.lower()
        for word in forbidden:
            if word in lower_text:
                raise ValidationError(f'Сообщение содержит запрещённое слово: {word}.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Attachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment to {self.message.id}"
