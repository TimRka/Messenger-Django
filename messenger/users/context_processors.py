# users/context_processors.py
from django.conf import settings
from .models import UserPreferences


def user_preferences(request):
    if request.user.is_authenticated:
        try:
            prefs = request.user.preferences
            return {
                'theme': prefs.theme,
                'font_family': prefs.font_family,
                'font_size': f"{prefs.font_size}px",
            }
        except:
            prefs = UserPreferences.objects.create(user=request.user)
            return {
                'theme': prefs.theme,
                'font_family': prefs.font_family,
                'font_size': f"{prefs.font_size}px",
            }
    return {'theme': 'light', 'font_family': 'system', 'font_size': '16px'}