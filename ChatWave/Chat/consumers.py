# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatRoomMessages

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.room_name = self.scope['url_route']['kwargs']['room_name']  #get the room name from the url

        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()


        
    async def disconnect(self, close_code):
        # Leave room group
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
            message=message
        )