from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Chat, Message, ChatMember
import json
import re
import logging
logger = logging.getLogger('chat')

User = get_user_model()

@login_required
def chat_list(request):
    user_chats = Chat.objects.filter(chatmember__user=request.user).prefetch_related('chatmember_set__user')
    return render(request, 'chat/chat_list.html', {'chats': user_chats})

@login_required
def create_chat(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        chat = Chat.objects.create(name=name)
        ChatMember.objects.create(chat=chat, user=request.user, role='admin')
        logger.info(f"User {request.user.username} created chat '{name}' (id={chat.id})")
        return redirect('chat:room', chat_id=chat.id)

    return render(request, 'chat/create_chat.html')



@login_required
def add_member(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    if not ChatMember.objects.filter(chat=chat, user=request.user, role='admin').exists():
        return HttpResponseForbidden("Only admin can add members")

    current_members = ChatMember.objects.filter(chat=chat).values_list('user_id', flat=True)
    chat_members = User.objects.filter(id__in=current_members)

    search_query = request.GET.get('search', '').strip()
    search_results = []

    if search_query:
        all_users = User.objects.exclude(id=request.user.id).exclude(id__in=current_members)

        is_email_search = '@' in search_query and '.' in search_query
        is_phone_search = any(char.isdigit() for char in search_query) and len(re.sub(r'\D', '', search_query)) >= 10
        phone_digits = re.sub(r'\D', '', search_query) if is_phone_search else None

        for user in all_users:
            include_in_results = False

            # Поиск по username
            if search_query.lower() in user.username.lower():
                include_in_results = True

            # Поиск по email
            if not include_in_results and is_email_search and user.email:
                if search_query.lower() in user.email.lower():
                    if user.can_see_email(request.user):
                        include_in_results = True

            # Поиск по телефону
            if not include_in_results and is_phone_search and user.phone:
                user_phone_digits = re.sub(r'\D', '', user.phone)
                if phone_digits in user_phone_digits or user_phone_digits in phone_digits:
                    if user.can_see_phone(request.user):
                        include_in_results = True

            if include_in_results:
                user.can_see_email_flag = user.can_see_email(request.user)
                user.can_see_phone_flag = user.can_see_phone(request.user)
                search_results.append(user)

        search_results = search_results[:20]

    if request.method == 'POST':
        username = request.POST.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
                if ChatMember.objects.filter(chat=chat, user=user).exists():
                    logger.warning(
                        f"Attempt to add existing member {username} to chat {chat_id} by {request.user.username}")
                    return render(request, 'chat/add_member.html', {
                        'chat': chat,
                        'error': f'Пользователь {username} уже в чате',
                        'search_query': search_query,
                        'search_results': search_results,
                        'chat_members': chat_members
                    })
                ChatMember.objects.create(chat=chat, user=user, role='member')
                logger.info(f"User {request.user.username} added {username} to chat {chat_id}")
                return redirect('chat:room', chat_id=chat.id)
            except User.DoesNotExist:
                logger.warning(
                    f"User {request.user.username} tried to add non-existent user '{username}' to chat {chat_id}")
                return render(request, 'chat/add_member.html', {
                    'chat': chat,
                    'error': f'Пользователь с username "{username}" не найден',
                    'search_query': search_query,
                    'search_results': search_results,
                    'chat_members': chat_members
                })

    return render(request, 'chat/add_member.html', {
        'chat': chat,
        'search_query': search_query,
        'search_results': search_results,
        'chat_members': chat_members
    })


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
    messages_qs = chat.messages.select_related('author').prefetch_related('attachments').order_by('id')

    if after_id:
        messages_qs = messages_qs.filter(id__gt=after_id)
    messages_qs = messages_qs[:100]

    data = []
    for m in messages_qs:
        attachments = []
        for att in m.attachments.all():
            attachments.append({
                'id': att.id,
                'file_url': att.file.url,
                'file_type': att.file_type,
                'original_name': att.original_name,
            })

        data.append({
            'id': m.id,
            'author': m.author.username,
            'text': m.text,
            'created_at': m.created_at.isoformat(),
            'attachments': attachments,
            'is_read': m.is_read,
        })

    return JsonResponse({'messages': data})

@login_required
@require_http_methods(["POST"])
@ensure_csrf_cookie
def send_message(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
        return JsonResponse({'error': 'Access denied'}, status=403)

    text = request.POST.get('text', '').strip()
    files = request.FILES.getlist('files')   # поддержка нескольких файлов

    if not text and not files:
        return JsonResponse({'error': 'Сообщение или файл обязателен'}, status=400)

    # Создаём сообщение
    message = Message(chat=chat, author=request.user)
    if text:
        message.text = text  # setter шифрует текст
    message.save()

    try:
        msg = Message(chat=chat, author=request.user, text=text)
        logger.info(f"User {request.user.username} sent message in chat {chat_id} (msg_id={msg.id})")
        msg.save()
    except ValidationError as e:
        logger.error(f"Validation error in chat {chat_id} by {request.user.username}: {e.messages}")
        return JsonResponse({'error': e.messages[0]}, status=400)
    except Exception as e:
        logger.exception(f"Unexpected error in send_message: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    # Сохраняем файлы
    for file in files:
        attachment = Attachment(message=message, file=file)
        attachment.save()

    # Подготавливаем данные для ответа
    attachments_data = [{
        'id': att.id,
        'file_url': att.file.url,
        'file_type': att.file_type,
        'original_name': att.original_name,
    } for att in message.attachments.all()]

    return JsonResponse({
        'message': {
            'id': message.id,
            'author': message.author.username,
            'text': message.text,
            'created_at': message.created_at.isoformat(),
            'attachments': attachments_data,
        }
    })


@login_required
def create_direct_chat(request, user_id):
    """Создание личного чата с пользователем"""
    try:
        other_user = get_object_or_404(User, id=user_id)

        user_chats = ChatMember.objects.filter(user=request.user).values_list('chat_id', flat=True)

        existing = ChatMember.objects.filter(
            chat_id__in=user_chats,
            user=other_user
        ).select_related('chat').first()

        if existing:
            chat_id = existing.chat_id
        else:
            chat_name = f"{request.user.username} & {other_user.username}"
            chat = Chat.objects.create(name=chat_name)

            ChatMember.objects.create(chat=chat, user=request.user, role='admin')
            ChatMember.objects.create(chat=chat, user=other_user, role='member')
            chat_id = chat.id

        return redirect('chat:room', chat_id=chat_id)

    except Exception as e:
        messages.error(request, f'Ошибка при создании чата: {str(e)}')
        return redirect('users:user_search')