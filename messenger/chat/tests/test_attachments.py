import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from chat.models import Chat, Message, Attachment, ChatMember


# ====================== FIXTURES ======================
@pytest.fixture
def test_user(django_user_model):
    return django_user_model.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )


@pytest.fixture
def chat(test_user):
    """Тестовый чат"""
    chat_obj = Chat.objects.create(name="Тестовый чат")
    ChatMember.objects.create(user=test_user, chat=chat_obj, role='admin')
    return chat_obj


@pytest.fixture
def auth_client(client, test_user):
    client.force_login(test_user)
    return client


# ====================== ТЕСТЫ ======================

@pytest.mark.django_db
def test_attachment_file_type_detection(test_user):
    """Проверка автоматического определения типа файла"""
    chat_obj = Chat.objects.create(name="Test")
    message = Message.objects.create(chat=chat_obj, author=test_user)

    # Изображение
    img = SimpleUploadedFile("photo.jpg", b"fake", content_type="image/jpeg")
    att = Attachment.objects.create(message=message, file=img)
    assert att.file_type == 'image'

    # Видео
    video = SimpleUploadedFile("video.mp4", b"fake", content_type="video/mp4")
    att = Attachment.objects.create(message=message, file=video)
    assert att.file_type == 'video'


@pytest.mark.django_db
def test_send_message_with_multiple_files(auth_client, chat):
    """Отправка сообщения + нескольких файлов"""
    url = reverse('chat:send_message', kwargs={'chat_id': chat.id})

    files = [
        SimpleUploadedFile("image1.jpg", b"fake1", content_type="image/jpeg"),
        SimpleUploadedFile("image2.png", b"fake2", content_type="image/png"),
    ]

    response = auth_client.post(url, {
        'text': 'Сообщение с несколькими файлами',
        'files': files
    }, format='multipart')

    assert response.status_code == 200

    message = Message.objects.last()
    assert message.text == 'Сообщение с несколькими файлами'
    assert message.attachments.count() == 2


@pytest.mark.django_db
def test_send_message_only_files(auth_client, chat):
    """Отправка только файлов (без текста)"""
    url = reverse('chat:send_message', kwargs={'chat_id': chat.id})

    image = SimpleUploadedFile("only_image.jpg", b"fake", content_type="image/jpeg")

    response = auth_client.post(url, {
        'files': [image]
    }, format='multipart')

    assert response.status_code == 200
    message = Message.objects.last()
    assert message.attachments.count() == 1


@pytest.mark.django_db
def test_send_message_validation_fails(auth_client, chat):
    """Нельзя отправить полностью пустое сообщение"""
    url = reverse('chat:send_message', kwargs={'chat_id': chat.id})

    response = auth_client.post(url, {}, format='multipart')

    assert response.status_code == 400


@pytest.mark.django_db
def test_get_messages_returns_attachments(auth_client, chat, test_user):
    """Проверка, что get_messages правильно возвращает вложения"""
    message = Message.objects.create(
        chat=chat,
        author=test_user,           # используем test_user вместо auth_client.user
        text="Смотри фото"
    )
    
    image = SimpleUploadedFile("test_photo.jpg", b"fake image", content_type="image/jpeg")
    Attachment.objects.create(message=message, file=image)

    url = reverse('chat:get_messages', kwargs={'chat_id': chat.id})
    response = auth_client.get(url)

    assert response.status_code == 200
    data = response.json()

    assert len(data['messages']) > 0
    
    # Находим наше сообщение
    msg = next((m for m in data['messages'] if m.get('text') == "Смотри фото"), None)
    assert msg is not None
    assert len(msg.get('attachments', [])) == 1
    assert msg['attachments'][0]['file_type'] == 'image'