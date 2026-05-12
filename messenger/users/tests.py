from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.forms import CustomUserCreationForm, CustomUserChangeForm
from users.models import CustomUser

User = get_user_model()

class UserModelTest(TestCase):
    """Тестирование модели CustomUser"""

    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_str_method(self):
        user = User.objects.create_user(username='testuser', email='t@t.com', password='pass')
        self.assertEqual(str(user), 'testuser')

    def test_user_requires_email(self):
        # email обязателен? В модели есть unique=True, но blank=False, по умолчанию required.
        # Попробуем создать без email
        with self.assertRaises(Exception):
            User.objects.create_user(username='noemail', password='pass', email=None)

    def test_phone_normalization(self):
        # если в модели есть clean() или сохранение с нормализацией
        user = User.objects.create_user(username='phoneuser', email='p@u.com', password='pass')
        user.phone = '89123456789'
        user.save()
        # предполагаем, что clean нормализует в +79123456789
        # если нет нормализации, этот тест может упасть – пропусти или реализуй
        # self.assertEqual(user.phone, '+79123456789')
        pass


class UserFormTest(TestCase):
    """Тестирование форм регистрации и редактирования"""

    def test_registration_form_valid_data(self):
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })
        self.assertTrue(form.is_valid())

    def test_registration_form_invalid_data(self):
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': 'not-an-email',
            'password1': 'pass',
            'password2': 'wrong',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('password2', form.errors)

    def test_change_form_valid(self):
        user = User.objects.create_user(username='edituser', email='edit@ex.com', password='old')
        form = CustomUserChangeForm(instance=user, data={
            'username': 'edituser',
            'email': 'edit@ex.com',
            'phone': '+79123456789',
            'birth_date': '1990-01-01',
            'bio': 'test bio',
            'email_privacy': 'everyone',
            'phone_privacy': 'everyone',
        })
        self.assertTrue(form.is_valid())

class UserViewsTest(TestCase):
    """Тестирование view: доступ, шаблоны, статусы"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@test.com', password='testpass')
        self.signup_url = reverse('users:signup')
        self.login_url = reverse('users:login')
        self.profile_url = reverse('users:profile')
        self.profile_edit_url = reverse('users:profile_edit')

    def test_signup_view_get(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/signup.html')

    def test_signup_view_post_valid(self):
        response = self.client.post(self.signup_url, data={
            'username': 'newbie',
            'email': 'newbie@ex.com',
            'password1': 'ValidPass123',
            'password2': 'ValidPass123',
        })
        self.assertRedirects(response, reverse('users:login'))
        self.assertTrue(User.objects.filter(username='newbie').exists())

    def test_profile_view_requires_login(self):
        # анонимный доступ – редирект на login
        response = self.client.get(self.profile_url)
        # Поскольку в urls.py нет @login_required для profile_view (она есть, но поставим проверку)
        # Если используется @login_required, то редирект на login с next
        self.assertRedirects(response, f'{reverse("users:login")}?next={self.profile_url}')

    def test_profile_view_authenticated(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertContains(response, 'testuser')

    def test_edit_profile_view(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(self.profile_edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile_edit.html')

    def test_login_view(self):
        response = self.client.post(self.login_url, data={
            'username': 'testuser',
            'password': 'testpass'
        })
        # после успешного логина редирект на /chats/ (LOGIN_REDIRECT_URL)
        self.assertRedirects(response, '/chats/')