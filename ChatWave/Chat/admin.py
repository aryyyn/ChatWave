from django.contrib import admin

from .models import *

admin.site.register(ChatRoom)
admin.site.register(Notification)
admin.site.register(UserLog)



class ChatRoomMessagesAdmin(admin.ModelAdmin):
    list_display = ('room', 'sender', 'message', 'created')  # Add the 'created' field here

admin.site.register(ChatRoomMessages, ChatRoomMessagesAdmin)
admin.site.register(Music)
