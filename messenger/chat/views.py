from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import Chat, Message, ChatMember
import json

# Это уже не нужно, так как используем кастомного пользователя
# class SignUpView(CreateView):
#     form_class = UserCreationForm
#     success_url = reverse_lazy('login')
#     template_name = 'registration/signup.html'

@login_required
def chat_list(request):
    user_chats = Chat.objects.filter(chatmember__user=request.user)
    return render(request, 'chat/chat_list.html', {'chats': user_chats})

@login_required
def chat_room(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
        return HttpResponseForbidden("You are not in this chat.")
    return render(request, 'chat/room.html', {'chat': chat})

@login_required
@require_http_methods(["GET"])
def get_messages(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
        return JsonResponse({'error': 'Access denied'}, status=403)

    after_id = request.GET.get('after')
    messages_qs = chat.messages.select_related('author').order_by('id')
    if after_id:
        messages_qs = messages_qs.filter(id__gt=after_id)
    messages_qs = messages_qs[:100]

    data = [{
        'id': m.id,
        'author': m.author.username,
        'text': m.text,
        'created_at': m.created_at.isoformat(),
    } for m in messages_qs]
    return JsonResponse({'messages': data})

@login_required
@require_http_methods(["POST"])
@ensure_csrf_cookie
def send_message(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not text:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)

    msg = Message(chat=chat, author=request.user, text=text)
    try:
        msg.save()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({
        'message': {
            'id': msg.id,
            'author': msg.author.username,
            'text': msg.text,
            'created_at': msg.created_at.isoformat(),
        }
    })