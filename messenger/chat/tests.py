from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from chat.models import Chat, ChatMember, Message

import json

User = get_user_model()

class ChatModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='u1@t.com', password='pass')
        self.user2 = User.objects.create_user(username='user2', email='u2@t.com', password='pass')
        self.chat = Chat.objects.create(name='Test Chat')

    def test_create_chat(self):
        self.assertEqual(self.chat.name, 'Test Chat')
        self.assertIsNotNone(self.chat.created_at)

    def test_str_method(self):
        self.assertEqual(str(self.chat), 'Test Chat')

    def test_chat_member(self):
        member = ChatMember.objects.create(chat=self.chat, user=self.user1, role='admin')
        self.assertEqual(str(member), 'user1 in Test Chat as admin')
        self.assertEqual(member.role, 'admin')

    def test_message_creation(self):
        msg = Message.objects.create(chat=self.chat, author=self.user1, text='Hello')
        self.assertEqual(msg.text, 'Hello')
        self.assertIsNotNone(msg.created_at)
        self.assertEqual(str(msg), 'user1: Hello')

    def test_message_validation_forbidden_words(self):
        # Проверка, что модель запрещает слова
        msg = Message(chat=self.chat, author=self.user1, text='ты редиска')
        with self.assertRaises(Exception):  # ValidationError
            msg.full_clean()
            msg.save()

    def test_message_max_length(self):
        long_text = 'x' * 2001
        msg = Message(chat=self.chat, author=self.user1, text=long_text)
        with self.assertRaises(Exception):
            msg.full_clean()
            msg.save()

class ChatViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='chatuser', email='ch@t.com', password='pass')
        self.other = User.objects.create_user(username='other', email='o@t.com', password='pass')
        self.chat = Chat.objects.create(name='Room')
        ChatMember.objects.create(chat=self.chat, user=self.user, role='admin')
        self.list_url = reverse('chat:list')
        self.create_url = reverse('chat:create')
        self.room_url = reverse('chat:room', args=[self.chat.id])
        self.add_member_url = reverse('chat:add_member', args=[self.chat.id])

    def test_chat_list_requires_login(self):
        response = self.client.get(self.list_url)
        self.assertRedirects(response, f'{reverse("users:login")}?next={self.list_url}')

    def test_chat_list_authenticated(self):
        self.client.login(username='chatuser', password='pass')
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/chat_list.html')
        self.assertContains(response, 'Room')

    def test_send_message_post(self):
        self.client.login(username='chatuser', password='pass')
        url = reverse('chat:send', args=[self.chat.id])
        response = self.client.post(url, data=json.dumps({'text': 'Hello'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['message']['text'], 'Hello')
        self.assertEqual(Message.objects.count(), 1)

    def test_send_message_empty(self):
        self.client.login(username='chatuser', password='pass')
        url = reverse('chat:send', args=[self.chat.id])
        response = self.client.post(url, data=json.dumps({'text': ''}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_send_message_forbidden_word(self):
        self.client.login(username='chatuser', password='pass')
        url = reverse('chat:send', args=[self.chat.id])
        response = self.client.post(url, data=json.dumps({'text': 'ты дурак'}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('запрещ', response.json()['error'].lower())

    def test_add_member_only_admin(self):
        self.client.login(username='other', password='pass')  # не админ
        response = self.client.get(self.add_member_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_add_member_admin(self):
        self.client.login(username='chatuser', password='pass')
        response = self.client.post(self.add_member_url, {'username': 'other'})
        self.assertRedirects(response, self.room_url)
        self.assertTrue(ChatMember.objects.filter(chat=self.chat, user=self.other).exists())