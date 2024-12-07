from django.shortcuts import render, get_object_or_404, redirect,HttpResponse
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
import random


@login_required
def chatView(request, chatroom):

   
    chat_room = get_object_or_404(ChatRoom, room_name=chatroom)
    chat_messages = chat_room.chat_messages.all().order_by('created')
    action = request.POST.get('action')
    status = "valid"
    
    
    if action == "next-song":
        songs =Music.objects.all()
        randomsong = random.choice(songs)
        
        context = {
            'chat_room': chat_room,
            'chat_messages': chat_messages,
            'songs': randomsong,
            'status': status,
        }
        
    else:
        songs = Music.objects.all()
        randomsong = random.choice(songs)
        
        context = {
            'chat_room': chat_room,
            'chat_messages': chat_messages,
         
            
        }
            
    return render(request, 'chat/chat.html', context)

@login_required
def chatHomeView(request):

    chat_rooms = ChatRoom.objects.all()
    sum = 0
    online_users = []
    for room in chat_rooms:
        sum = sum + room.online_count
        online_users += room.online_users

    total_online_users = sum
    context = {
        'total_online_users': total_online_users,
        'online_users': online_users
    }

    # if request.method == "POST":
    #     action = request.POST.get('action')
        
    return render(request, 'chat/chathome.html', context)