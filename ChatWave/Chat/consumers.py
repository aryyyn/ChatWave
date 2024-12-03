# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatRoomMessages
import datetime
from django.db.models import F, Q

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.room_name = self.scope['url_route']['kwargs']['room_name']  #get the room name from the url

        await self.update_online_user_count("connect", self.room_name, self.scope["user"].username)

        self.room_group_name = f'chat_{self.room_name}'



        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        chat_room = await database_sync_to_async(ChatRoom.objects.get)(room_name=self.room_name)
        
  

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'online_count',
                'online_count': chat_room.online_count,
                'online_users': chat_room.online_users,
                'identifier': 'joined',
                'recently_joined':self.scope["user"].username 
            }
        )


    async def online_count(self, event):
        online_count = event['online_count']
        online_users = event['online_users']
        recently_joined = event['recently_joined']
        identifier = event['identifier']
        
        await self.send(text_data=json.dumps({

            'type': 'online_count',
            'identifier': identifier,
            'online_count': online_count,
            'online_users': online_users,
            'recently_joined': recently_joined
        }))

        
    async def disconnect(self, close_code):
        
        await self.update_online_user_count("disconnect", self.room_name , self.scope["user"].username)

        chat_room = await database_sync_to_async(ChatRoom.objects.get)(room_name=self.room_name)


        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'online_count',
                'online_count': chat_room.online_count,
                'online_users': chat_room.online_users,
                'identifier': 'left',
                'recently_joined':self.scope["user"].username 
            }
        )


        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )



    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # Save message to database
        # await self.save_message(message)
        
        #save the message to the database
        await self.save_message(message)

        #send the message to a specific group (chat_message is automatically called)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message', #can also use type as notification if we want to send notifications to the user
                'message': message,
                'username': self.scope["user"].username,
            }
        )


    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        #send the message via websocket to the frontend
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
        }))
        
        
    #save_message function that can be called to save the message to the database   
    @database_sync_to_async
    def save_message(self, message):
        room = ChatRoom.objects.get(room_name=self.room_name)
        ChatRoomMessages.objects.create(
            room=room,
            sender=self.scope["user"],
            message=message,
            # created = datetime.datetime.now() #not needed since models.py already handles it
        )




    @database_sync_to_async
    def update_online_user_count(self, status, room_name, username):
        chat_room = ChatRoom.objects.get(room_name=room_name)
        if status == "connect":
            if username not in chat_room.online_users:
                chat_room.online_count = F('online_count') + 1
                chat_room.online_users.append(username)
            chat_room.save()   
           
        elif status == "disconnect":
            if username in chat_room.online_users:
                chat_room.online_count = F('online_count')-1
                chat_room.online_users.remove(username)
            chat_room.save()



 

        
        ChatRoom.objects.filter(room_name=room_name, online_count__lt=0).update(online_count=0)  #prevents the online count to drop to a negative value

    