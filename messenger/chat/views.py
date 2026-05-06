from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.db import models
from .models import Chat, Message, ChatMember
import json

User = get_user_model()

@login_required
def chat_list(request):
    user_chats = Chat.objects.filter(chatmember__user=request.user)
    return render(request, 'chat/chat_list.html', {'chats': user_chats})

@login_required
def create_chat(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        chat = Chat.objects.create(name=name)
        ChatMember.objects.create(chat=chat, user=request.user, role='admin')
        return redirect('chat:room', chat_id=chat.id)

    return render(request, 'chat/create_chat.html')


@login_required
def add_member(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    # только админ может добавлять
    if not ChatMember.objects.filter(chat=chat, user=request.user, role='admin').exists():
        return HttpResponseForbidden("Only admin can add members")

    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
            ChatMember.objects.get_or_create(chat=chat, user=user, defaults={'role': 'member'})
            return redirect('chat:room', chat_id=chat.id)
        except User.DoesNotExist:
            return render(request, 'chat/add_member.html', {'chat': chat, 'error': 'User not found'})

    return render(request, 'chat/add_member.html', {'chat': chat})


@login_required
def chat_room(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
        return HttpResponseForbidden("You are not in this chat.")

    is_admin = ChatMember.objects.filter(chat=chat, user=request.user, role='admin').exists()

    return render(request, 'chat/room.html', {
        'chat': chat,
        'is_admin': is_admin
    })
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