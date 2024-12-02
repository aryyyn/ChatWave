from django.shortcuts import render, get_object_or_404, redirect,HttpResponse
from .models import *
from .forms import *

def chatView(request, chatroom):
    chat_room = get_object_or_404(ChatRoom, room_name=chatroom)
    chat_messages = chat_room.chat_messages.all().order_by('created')[:50]
    
    context = {
        'chat_room': chat_room,
        'chat_messages': chat_messages,
    }
    
    return render(request, 'chat/chathome.html', context)