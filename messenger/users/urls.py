from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from .views import SignUpView, profile_view, profile_edit_view, user_search, settings_view, set_theme
from .forms import CustomAuthenticationForm



app_name = 'users'

urlpatterns = [
    #АУТЕНТИФИКАЦИЯ
    path('login/', auth_views.LoginView.as_view(
        template_name='users/login.html',
        authentication_form=CustomAuthenticationForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),


    #ПРОФИЛЬ НАСТРОЙКИ
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', profile_edit_view, name='profile_edit'),
    path('search/', user_search, name='user_search'),
    path('settings/', settings_view, name='settings'),
    path('set-theme/', set_theme, name='set_theme'),

    #ПАРОЛЬ РЕСЕТ
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset_form.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt',
             success_url=reverse_lazy('users:password_reset_done')
         ), 
         name='password_reset'),

    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url=reverse_lazy('users:password_reset_complete')
         ), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]