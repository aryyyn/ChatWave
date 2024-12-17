# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatRoomMessages, Music
from Auth.models import *
from Profile.models import Playlists
import datetime
import random
from django.db.models import F, Q


from django.shortcuts import get_object_or_404

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

        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
           
            
            if message_type == 'song':
                songResult = await self.addSong(text_data_json['song'])
               

                await self.send(
                    text_data=json.dumps({
                        'type': 'songResult',  
                        'songResult': songResult
                    })
                )
                          
            elif message_type == "delete_message":
              
                message_id = text_data_json.get("message_id")
               
         
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'delete_message',
                        'message_id': message_id,
                       
                    }
                )

            elif message_type == "change_song":
                print("working")
                
                randomsong = await self.getRandomMusic()
                await self.send(text_data=json.dumps({
                    'type': "change_song",
                    'song_title': randomsong.title,
                    'song_artist': randomsong.artist,
                    'song_thumbnail': randomsong.thumbnail.url,
                    'song': randomsong.song.url,

                }))
                #will modify the logic for this once the model has been integrated
                

                
            else:

                message = text_data_json['message']
                ChatRoomName = text_data_json['ChatRoom']
                
                chat_room = await self.getChatRoomObject(ChatRoomName)

                if chat_room.category == "Other" and message.startswith("/add"):
                    
                    chatRoomOwnerUsername = ChatRoomName.split("_")[0]
                    toAddUsername = message.split(' ')[1]
                    if self.scope["user"].username == chatRoomOwnerUsername and self.scope["user"].username!= toAddUsername :             
                        
                        addUserResult = await self.add_user_chatroom(toAddUsername, chat_room)

                        await self.send(text_data=json.dumps({
                            'type': 'add_update',
                            'addUserResult': addUserResult,
                            

                        }))

                        
                   

                elif chat_room.category == "Other" and message.startswith("/remove"):
                    chatRoomOwnerUsername = ChatRoomName.split("_")[0]
                    toRemoveUsername = message.split(' ')[1]
                    if self.scope["user"].username == chatRoomOwnerUsername and self.scope["user"].username != toRemoveUsername:
                        
                        removeUserResult = await self.remove_user_chatroom(toRemoveUsername, chat_room)

                        await self.send(text_data=json.dumps({
                            'type': 'remove_update',
                            'removeUserResult': removeUserResult,
                            

                        }))

                        await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'remove_update_all',
                            'toRemoveUsername': toRemoveUsername


                        }
                        )
                else:
                    
                    messageObject = await self.save_message(message)

                    #send the message to a specific group (chat_message is automatically called)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message', #can also use type as notification if we want to send notifications to the user
                            'message': message,
                            'username': self.scope["user"].username,
                            'profilePicture': self.scope["user"].profilePicture,
                            'messageID': messageObject.id,
                            
                        
                        }
                    )
        except Exception as err:
            print(err)



    async def delete_message(self, event):
        
        message_id = event['message_id']
      
        
        await self.send(text_data=json.dumps({
            "type": "delete_message",
            "message_id": message_id,
           

        }))


    
    
    async def remove_update_all(self, event):
        toRemoveUsername = event['toRemoveUsername']
        await self.send(text_data=json.dumps({
            "type": "remove_update_all",
            "updateUsername": toRemoveUsername,
           
        }))


    @database_sync_to_async
    def getRandomMusic(self):
        songs = Music.objects.all()
        randomsong = random.choice(songs)
        print(randomsong)
        return randomsong



    @database_sync_to_async 
    def getChatRoomObject(self, ChatRoomName):
        return ChatRoom.objects.filter(room_name=ChatRoomName).first()

    @database_sync_to_async
    def add_user_chatroom(self, username, chat_room):
        
        User = CustomUser.objects.filter(username=username).first()
        if (User):
            chat_room.allowed.append(username)
            chat_room.save()
            return "User Added"
        else:
            return "No User Found"
        
    @database_sync_to_async
    def remove_user_chatroom(self, username, chat_room):
       
        User = CustomUser.objects.filter(username=username).first()
        if (User):
            if username in chat_room.allowed:
                chat_room.allowed.remove(username)
                chat_room.save()
                return "User Removed"
            else:
                return "User Doesn't Have Access"
           
        else:
            return "No User Found"


        #check if the user actually exists
        #add the user to the chatroom
        

    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        profilePicture = event['profilePicture']
        messageID = event['messageID']

        #send the message via websocket to the frontend
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'profilePicture': profilePicture,
            'messageID': messageID
        }))
        
        
    #save_message function that can be called to save the message to the database   
    @database_sync_to_async
    def save_message(self, message):
        room = ChatRoom.objects.get(room_name=self.room_name)
        MessageObject = ChatRoomMessages.objects.create(
            room=room,
            sender=self.scope["user"],
            message=message,
            # created = datetime.datetime.now() #not needed since models.py already handles it
        )
        return MessageObject
    

    




    @database_sync_to_async
    def addSong(self,song):
        isMusic = Music.objects.filter(title=song).exists()
        
        if (isMusic):
            music = Music.objects.get(title = song)
            playlist = Playlists.objects.filter(user=self.scope["user"], playlist_name=music.genre).first()
            if playlist:
           
                current_songs = playlist.songs.split(",") if playlist.songs else []
                if song in current_songs:
                    return "Present"
                else:
                    current_songs.append(song)
                    playlist.songs = ",".join(current_songs)
                    playlist.save()
                    return "Absent"


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

    