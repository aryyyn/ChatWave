from django.shortcuts import render,redirect
from Auth.models import *
from Chat.models import ChatRoomMessages
from django.contrib.auth.decorators import login_required
@login_required
def profileHome(request, username):

    userinfo = request.user
    checkusername = CustomUser.objects.filter(username=username).exists()

    if checkusername:
        messagecount = ChatRoomMessages.objects.filter(sender__username=username).count()
        context = {
                "userinfo": CustomUser.objects.get(username=username),
                "messagecount": messagecount

            }
            
        return render(request, "profile.html", context=context)    
    
     
    else:
      
        
        context = {
                "status": "NotFound"
            }
        return render(request, "profile.html", context=context) 