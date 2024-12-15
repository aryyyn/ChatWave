from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
import random
from django.contrib import messages
from django.http import JsonResponse


@login_required
def deleteMessage(request, chatroom, messageid):
    if request.method == "POST":
        try:
            message = get_object_or_404(ChatRoomMessages, id=messageid)
            if message.sender != request.user:
                return JsonResponse(
                    {"success": False, "error": "Unauthorized"}, status=403
                )
            message.delete()
            return JsonResponse({"success": True})
        except Exception as err:
            print(err)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


@login_required
def chatView(request, chatroom):



    chat_room = get_object_or_404(ChatRoom, room_name=chatroom)

    if chat_room.category == "Other": 
        if request.user.username not in chat_room.allowed:
            return redirect(chatView, chatroom="General_Chat")

    
    chat_messages = chat_room.chat_messages.all().order_by("created")
    ChatRoomOther = ChatRoom.objects.filter(category="Other")
    action = request.POST.get("action")
    status = "valid"



    if action == "add-room":
        songs = Music.objects.all()
        randomsong = random.choice(songs)
        username = request.user.username
        ChatRoomName = f"{username}_chatroom"

        ChatRoomObject = ChatRoom.objects.filter(room_name=ChatRoomName).first()

        if not ChatRoomObject:
            ChatRoomObj = ChatRoom.objects.create(room_name=ChatRoomName, online_count=0, category="Other", allowed = [username])
            return redirect(chatView, chatroom=ChatRoomName)
            
                
        else:
            return redirect(chatView, chatroom=ChatRoomName)

    elif action == "next-song":
        songs = Music.objects.all()
        randomsong = random.choice(songs)

        context = {
            "chat_room": chat_room,
            "chat_messages": chat_messages,
            "songs": randomsong,
            "status": status,
            "ChatRoomOther": ChatRoomOther,
        }
        return render(request, "chat/chat.html", context)

    
    songs = Music.objects.all()
    randomsong = random.choice(songs)
    
    

    context = {
        "chat_room": chat_room,
        "chat_messages": chat_messages,
        "ChatRoomOther": ChatRoomOther,
    }
    return render(request, "chat/chat.html", context)


@login_required
def chatHomeView(request):

    chat_rooms = ChatRoom.objects.all()
    sum = 0
    online_users = []
    for room in chat_rooms:
        sum = sum + room.online_count
        online_users += room.online_users

    total_online_users = sum
    context = {"total_online_users": total_online_users, "online_users": online_users}

    # if request.method == "POST":
    #     action = request.POST.get('action')

    return render(request, "chat/chathome.html", context)
