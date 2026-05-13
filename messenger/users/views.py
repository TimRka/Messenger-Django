from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from .forms import UserPreferencesForm
from .models import UserPreferences
import json
from django.http import JsonResponse
import re
import logging
logger = logging.getLogger('users')


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('users:login')
    template_name = 'users/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(f"New user registered: {self.object.username} (id={self.object.id})")
        return response

    def form_invalid(self, form):
        logger.warning(f"Registration failed: {form.errors}")
        return super().form_invalid(form)

@login_required
def profile_view(request, username=None):
    """Просмотр профиля пользователя"""
    if username:
        user = get_object_or_404(CustomUser, username=username)
    else:
        user = request.user

    # Добавляем флаги приватности для просматриваемого пользователя
    user.can_see_email_flag = user.can_see_email(request.user)
    user.can_see_phone_flag = user.can_see_phone(request.user)

    return render(request, 'users/profile.html', {'user': user})


@login_required
def profile_edit_view(request):
    """Редактирование профиля пользователя"""
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            logger.info(f"User {request.user.username} updated profile")
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('users:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
        logger.warning(f"User {request.user.username} profile edit failed: {form.errors}")
    return render(request, 'users/profile_edit.html', {'form': form})


@login_required
def user_search(request):
    search_query = request.GET.get('q', '').strip()
    logger.info(f"User {request.user.username} searched for '{search_query}'")
    users = []

    if search_query:
        all_users = CustomUser.objects.exclude(id=request.user.id)

        is_email_search = '@' in search_query and '.' in search_query
        is_phone_search = any(char.isdigit() for char in search_query) and len(re.sub(r'\D', '', search_query)) >= 10
        phone_digits = re.sub(r'\D', '', search_query) if is_phone_search else None

        for user in all_users:
            include_in_results = False

            if search_query.lower() in user.username.lower():
                include_in_results = True

            if not include_in_results and is_email_search and user.email:
                if search_query.lower() in user.email.lower():
                    if user.can_see_email(request.user):
                        include_in_results = True

            if not include_in_results and is_phone_search and user.phone:
                user_phone_digits = re.sub(r'\D', '', user.phone)
                if phone_digits in user_phone_digits or user_phone_digits in phone_digits:
                    if user.can_see_phone(request.user):
                        include_in_results = True

            if include_in_results:
                user.can_see_email_flag = user.can_see_email(request.user)
                user.can_see_phone_flag = user.can_see_phone(request.user)
                users.append(user)

        users = users[:20]

    context = {
        'search_query': search_query,
        'users': users,
    }
    return render(request, 'users/user_search.html', context)

@login_required
def settings_view(request):
    prefs, created = UserPreferences.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserPreferencesForm(request.POST, instance=prefs)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки успешно сохранены!')
            return redirect('users:settings')
    else:
        form = UserPreferencesForm(instance=prefs)
    
    context = {'form': form}
    return render(request, 'users/settings.html', context)


@login_required
def set_theme(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            theme = data.get('theme')
            if theme in ['light', 'dark', 'fire', 'high_contrast', 'sepia']:
                prefs = request.user.preferences
                prefs.theme = theme
                prefs.save()
                return JsonResponse({'status': 'success'})
        except:
            pass
    return JsonResponse({'status': 'error'}, status=400)