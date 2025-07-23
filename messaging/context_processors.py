from .models import Conversation, Message

def unread_messages(request):
    if request.user.is_authenticated:
        conversations = Conversation.objects.filter(participants=request.user)
        unread_count = Message.objects.filter(
            conversation__in=conversations,
            is_read=False
        ).exclude(sender=request.user).count()
        return {'unread_messages': unread_count}
    return {'unread_messages': 0}