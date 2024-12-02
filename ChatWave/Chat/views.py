from django.shortcuts import render, get_object_or_404, redirect,HttpResponse
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required



@login_required
def chatView(request, chatroom):
    chat_room = get_object_or_404(ChatRoom, room_name=chatroom)
    chat_messages = chat_room.chat_messages.all().order_by('created')[:50]
    
    context = {
        'chat_room': chat_room,
        'chat_messages': chat_messages,
    }
    
    return render(request, 'chat/chat.html', context)

@login_required
def chatHomeView(request):

    if request.method == "POST":
        action = request.POST.get('action')
        
    return render(request, 'chat/chathome.html',)