from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from cryptography.fernet import Fernet


class Chat(models.Model):
    name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Chat {self.id}"


class ChatMember(models.Model):
    ROLE_CHOICES = [('member', 'Member'), ('admin', 'Admin')]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')

    class Meta:
        unique_together = [['user', 'chat']]

    def __str__(self):
        return f"{self.user.username} in {self.chat}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    _text = models.TextField(db_column='text', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    @property
    def text(self):
        if not self._text:
            return ''
        f = Fernet(settings.ENCRYPTION_KEY)
        return f.decrypt(self._text.encode()).decode()

    @text.setter
    def text(self, value):
        if value:
            f = Fernet(settings.ENCRYPTION_KEY)
            self._text = f.encrypt(value.encode()).decode()
        else:
            self._text = ''

    def __str__(self):
        return f"{self.author.username}: {self.text[:30] if self.text else 'Attachment'}"


class Attachment(models.Model):
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
    ]

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(
        upload_to='attachments/%Y/%m/%d/', 
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp', 
                                  'mp4', 'webm', 'mov', 'mp3', 'wav', 'ogg', 'm4a',
                                  'pdf', 'doc', 'docx', 'txt', 'zip'])
        ]
    )
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, blank=True)
    original_name = models.CharField(max_length=255, blank=True)  # сохраняем оригинальное имя
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Автоматическое определение типа файла
        if self.file and not self.file_type:
            filename = self.file.name.lower()
            if any(ext in filename for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                self.file_type = 'image'
            elif any(ext in filename for ext in ['.mp4', '.webm', '.mov']):
                self.file_type = 'video'
            elif any(ext in filename for ext in ['.mp3', '.wav', '.ogg', '.m4a']):
                self.file_type = 'audio'
            else:
                self.file_type = 'document'

        # Сохраняем оригинальное имя файла
        if self.file and not self.original_name:
            self.original_name = self.file.name.split('/')[-1]

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.file_type} to message {self.message.id}"