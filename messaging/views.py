from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.contrib import messages
from .models import Conversation, Message, MessageRead

User = get_user_model()

@login_required
def conversation_list(request):
    conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')
    conversation_data = []
    for conversation in conversations:
        recipient = conversation.participants.exclude(id=request.user.id).first()
        has_unread_messages = conversation.messages.filter(is_read=False).exclude(sender=request.user).exists()
        conversation_data.append({
            'conversation': conversation,
            'recipient': recipient,
            'has_unread_messages': has_unread_messages
        })
    context = {
        'conversation_data': conversation_data
    }
    return render(request, 'messaging/list.html', context)

@login_required
def start_conversation(request, user_id=None):
    if user_id is not None:
        # Cas où l'URL contient un user_id (par exemple, /messaging/start/3/)
        recipient = get_object_or_404(User, id=user_id)
        
        if recipient == request.user:
            messages.error(request, "Vous ne pouvez pas démarrer une conversation avec vous-même.")
            return redirect('messaging:conversation_list')
        
        # Vérifier si une conversation existe déjà
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=recipient
        ).first()
        
        if not conversation:
            # Créer une nouvelle conversation
            conversation = Conversation.objects.create(subject="Nouvelle conversation")
            conversation.participants.add(request.user, recipient)
        
        # Rediriger vers la page de détail de la conversation
        return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    
    # Gestion des requêtes POST (cas actuel depuis seller_profile_public.html)
    if request.method == 'POST':
        try:
            data = request.POST
            recipient_id = data.get('recipient_id')
            if not recipient_id:
                return JsonResponse({
                    'success': False,
                    'error': "L'ID du destinataire est requis."
                }, status=400)
            
            recipient = get_object_or_404(User, id=recipient_id)
            
            if recipient == request.user:
                return JsonResponse({
                    'success': False,
                    'error': "Vous ne pouvez pas démarrer une conversation avec vous-même."
                }, status=400)
            
            # Vérifier si une conversation existe déjà
            conversation = Conversation.objects.filter(
                participants=request.user
            ).filter(
                participants=recipient
            ).first()
            
            if not conversation:
                # Créer une nouvelle conversation
                conversation = Conversation.objects.create(subject="Nouvelle conversation")
                conversation.participants.add(request.user, recipient)
            
            return JsonResponse({
                'success': True,
                'conversation_id': conversation.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    # Si ni POST ni user_id, rediriger vers la liste des conversations
    return redirect('messaging:conversation_list')

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    # Marquer les messages non lus comme lus pour l'utilisateur actuel
    unread_messages = conversation.messages.filter(is_read=False).exclude(sender=request.user)
    for message in unread_messages:
        MessageRead.objects.get_or_create(message=message, user=request.user)
        message.is_read = True
        message.save()
    
    context = {
        'conversation': conversation,
        'recipient': conversation.participants.exclude(id=request.user.id).first()
    }
    return render(request, 'messaging/conversation.html', context)

@login_required
@require_POST
def send_message(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    content = request.POST.get('content')
    attachment = request.FILES.get('attachment')
    
    if not content and not attachment:
        messages.error(request, "Le message ne peut pas être vide.")
        return redirect('messaging:conversation_detail', conversation_id=conversation_id)
    
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content or "",
        attachment=attachment
    )
    
    # Mettre à jour le champ updated_at de la conversation
    conversation.updated_at = message.created_at
    conversation.save()
    
    messages.success(request, "Message envoyé avec succès.")
    return redirect('messaging:conversation_detail', conversation_id=conversation_id)