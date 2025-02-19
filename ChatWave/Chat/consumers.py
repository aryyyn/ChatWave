# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatRoomMessages, Music, Notification, UserLog
from Auth.models import *
from Profile.models import Playlists
import datetime
import random
from django.db.models import F, Q
import joblib
import os
import spacy
from django.shortcuts import get_object_or_404
from cryptography.fernet import Fernet

_key_cache = None 


class ChatConsumer(AsyncWebsocketConsumer):
    model = None
    vectorizer = None
    nlp = None

    async def connect(self):
        if not ChatConsumer.model:
            ChatConsumer.model = joblib.load("../Model/WordFilterFiles/text_classifier_model.pkl")
            ChatConsumer.vectorizer = joblib.load("../Model/WordFilterFiles/vectorizer.pkl")
            ChatConsumer.nlp = spacy.load("en_core_web_sm")
        
        self.model = ChatConsumer.model
        self.vectorizer = ChatConsumer.vectorizer
        self.nlp = ChatConsumer.nlp

        self.room_name = self.scope["url_route"]["kwargs"][
            "room_name"
        ]  # get the room name from the url

        await self.update_online_user_count(
            "connect", self.room_name, self.scope["user"].username
        )

        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        chat_room = await database_sync_to_async(ChatRoom.objects.get)(
            room_name=self.room_name
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "online_count",
                "online_count": chat_room.online_count,
                "online_users": chat_room.online_users,
                "identifier": "joined",
                "recently_joined": self.scope["user"].username,
            },
        )

    async def online_count(self, event):
        online_count = event["online_count"]
        online_users = event["online_users"]
        recently_joined = event["recently_joined"]
        identifier = event["identifier"]

        await self.send(
            text_data=json.dumps(
                {
                    "type": "online_count",
                    "identifier": identifier,
                    "online_count": online_count,
                    "online_users": online_users,
                    "recently_joined": recently_joined,
                }
            )
        )

    async def disconnect(self, close_code):

        await self.update_online_user_count(
            "disconnect", self.room_name, self.scope["user"].username
        )

        chat_room = await database_sync_to_async(ChatRoom.objects.get)(
            room_name=self.room_name
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "online_count",
                "online_count": chat_room.online_count,
                "online_users": chat_room.online_users,
                "identifier": "left",
                "recently_joined": self.scope["user"].username,
            },
        )

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):

        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type")

            if message_type == "song":
                songResult = await self.addSong(text_data_json["song"])

                await self.send(
                    text_data=json.dumps(
                        {"type": "songResult", "songResult": songResult}
                    )
                )

            elif message_type == "typeindicator":

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "type_indicator",
                        "username": text_data_json.get("username"),
                    },
                )

            elif message_type == "delete_notification":
                notification_id = text_data_json.get("notification_id")
                await self.delete_notification(notification_id)

            elif message_type == "stopped_typing":

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "stopped_typing",
                    },
                )

            elif message_type == "delete_message":

                message_id = text_data_json.get("message_id")

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "delete_message",
                        "message_id": message_id,
                    },
                )

            elif message_type == "change_song":
       
                genre = text_data_json.get("genre")

                randomsong = await self.getRandomMusic(genre)
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "change_song",
                            "song_title": randomsong.title,
                            "song_artist": randomsong.artist,
                            "song_thumbnail": randomsong.thumbnail.url,
                            "song": randomsong.song.url,
                        }
                    )
                )
                # will modify the logic for this once the model has been integrated

            else:

                message = text_data_json["message"]
                ChatRoomName = text_data_json["ChatRoom"]
                notification_info = {}

                doc = self.nlp(message)
                filtered_message = " ".join(
                    [word.text for word in doc if not word.is_stop]
                )

                split_message = filtered_message.split(" ")
                bad_words_message = {}

                for word in split_message:
                    vectorized_input = self.vectorizer.transform([word])
                    prediction = self.model.predict(vectorized_input)
                    bad_words_message.update(
                        {word: prediction}
                    )  # get the filtered words and create a dict

                # print(bad_words_message)
                words = message.split(" ")
                filtered_message = []
                filtered_words = []
                for w in words:
                    if w.startswith("@"):
                        tobeMentioned = w.split("@")[1]
                        userMentioned = await self.getMentionedUser(tobeMentioned)

                        print(userMentioned)
                        
                        if userMentioned:
                            # Check if the user mentioned in this message is the same as the user who sent it.
                            messageUsername = self.scope["user"].username
                            if not (tobeMentioned == messageUsername):
                                notification_text = f"You were mentioned by {messageUsername} in ChatRoom {ChatRoomName}"
                                notification_id = await self.createNotification(
                                    notification_text, userMentioned
                                )
                                notification_info['is_notification'] = True  
                                notification_info['mentionedUser'] = userMentioned.username
                                notification_info['notification_text'] = notification_text
                                notification_info['notification_id'] = notification_id
                               

                              

                            # add notifications to the users who were pinged
                            else:
                                print("no user found with that username")

                    if w in bad_words_message and bad_words_message[w] == "bad":
                        lettercount = len(w)
                        filtered_message.append("*" * lettercount)
                        filtered_words.append(w)
                    else:
                        filtered_message.append(w)

                

                message = " ".join(filtered_message)

                chat_room = await self.getChatRoomObject(ChatRoomName)

                if chat_room.category == "Other" and message.startswith("/leave"):

                    chatRoomOwnerUsername = ChatRoomName.split("_")[0]
                    messageUsername = self.scope["user"].username

                    if chatRoomOwnerUsername != messageUsername:
                        leave_chat_room = await self.leaveChatRoom(chat_room, messageUsername)
                        await self.send(
                            text_data=json.dumps(
                                {
                                    "type": "leave_update",
                                    "leave_update_result": leave_chat_room
                                }
                            )
                        )
            
                if chat_room.category == "Other" and message.startswith("/delete"):
                    chatRoomOwnerUsername = ChatRoomName.split("_")[0]
                    usernames_in_chatroom = await self.usernames_in_chatroom(chat_room)
                    if (self.scope["user"].username == chatRoomOwnerUsername):
                        removeChatRoom = await self.remove_chat_room (
                            chat_room
                        )
                        await self.send(
                            text_data=json.dumps(
                                {
                                    'type': 'remove_chatroom',
                                    'remove_chatroom_result': removeChatRoom,
                                }
                            )
                        )

                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                "type": "remove_chatroom_all",
                                "usernames_in_chatroom": usernames_in_chatroom,
                            },
                        )
                    


                elif chat_room.category == "Other" and message.startswith("/add"):

                    chatRoomOwnerUsername = ChatRoomName.split("_")[0]
                    toAddUsername = message.split(" ")[1]
                    if (
                        self.scope["user"].username == chatRoomOwnerUsername
                        and self.scope["user"].username != toAddUsername
                    ):

                        addUserResult = await self.add_user_chatroom(
                            toAddUsername, chat_room
                        )

                        await self.send(
                            text_data=json.dumps(
                                {
                                    "type": "add_update",
                                    "addUserResult": addUserResult,
                                }
                            )
                        )

                elif chat_room.category == "Other" and message.startswith("/remove"):
                    chatRoomOwnerUsername = ChatRoomName.split("_")[0]
                    toRemoveUsername = message.split(" ")[1]
                    if (
                        self.scope["user"].username == chatRoomOwnerUsername
                        and self.scope["user"].username != toRemoveUsername
                    ):

                        removeUserResult = await self.remove_user_chatroom(
                            toRemoveUsername, chat_room
                        )

                        await self.send(
                            text_data=json.dumps(
                                {
                                    "type": "remove_update",
                                    "removeUserResult": removeUserResult,
                                }
                            )
                        )

                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                "type": "remove_update_all",
                                "toRemoveUsername": toRemoveUsername,
                            },
                        )
                else:

                    messageObject = await self.save_message(message, filtered_words)

                    # send the message to a specific group (chat_message is automatically called)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "chat_message",  # can also use type as notification if we want to send notifications to the user
                            "message": message,
                            "username": self.scope["user"].username,
                            "profilePicture": self.scope["user"].profilePicture,
                            "messageID": messageObject.id,
                            "notification_info": notification_info
                        },
                    )
        except Exception as err:
            print(err)

    async def delete_message(self, event):

        message_id = event["message_id"]
        await self.save_logs(self.scope["user"], f"Deleted their message")
        await self.send(
            text_data=json.dumps(
                {
                    "type": "delete_message",
                    "message_id": message_id,
                }
            )
        )

    async def type_indicator(self, event):
        username = event["username"]

        await self.send(
            text_data=json.dumps({"type": "typeindicator", "username": username})
        )

    async def remove_chatroom_all(self,event):
        users_in_chatroom = event["usernames_in_chatroom"]
        await self.send(
            text_data=json.dumps({
                "type": "remove_chatroom_all",
                "users_in_chatroom": users_in_chatroom,
            })
        )

    async def stopped_typing(self, event):

        await self.send(text_data=json.dumps({"type": "stopped_typing"}))

    async def remove_update_all(self, event):
        toRemoveUsername = event["toRemoveUsername"]
        await self.send(
            text_data=json.dumps(
                {
                    "type": "remove_update_all",
                    "updateUsername": toRemoveUsername,
                }
            )
        )

    @database_sync_to_async
    def getRandomMusic(self, genre):
        SentimentSong = Music.objects.filter(genre=genre)
        randomSentimentSong = random.choice(SentimentSong)
        # print(randomsong)
        return randomSentimentSong

    @database_sync_to_async
    def getMentionedUser(self, username):
        user = CustomUser.objects.filter(username=username).first()
        return user

    @database_sync_to_async
    def createNotification(self, notification_text, userMentioned):
        notification = Notification.objects.create(
            notification_text=notification_text, user=userMentioned
        )
        return notification.id

    @database_sync_to_async
    def usernames_in_chatroom(self, chat_room):
        return chat_room.allowed
        

    @database_sync_to_async
    def getChatRoomObject(self, ChatRoomName):
        return ChatRoom.objects.filter(room_name=ChatRoomName).first()

    @database_sync_to_async
    def add_user_chatroom(self, username, chat_room):

        User = CustomUser.objects.filter(username=username).first()
        if User:
            chat_room.allowed.append(username)
            chat_room.save()
            UserLog.objects.create(user=self.scope["user"], action=f"Added {username} to their chatroom at")
        
            return "User Added"
        
        else:
            return "No User Found"
        

    @database_sync_to_async
    def delete_notification(self, notification_id):
       test = Notification.objects.get(id = notification_id)
       test.delete()
        
    @database_sync_to_async
    def remove_chat_room(self, chat_room):
        deleted_count, _ = chat_room.delete()
        if (deleted_count > 0):
            UserLog.objects.create(user=self.scope["user"], action=f"Removed their chatroom")
            return ("Chat Room has been deleted.")
        
        else:
            return ("Chat Room can not be deleted.")
        
        
    @database_sync_to_async
    def leaveChatRoom(self, chat_room, messageUsername):
        chat_room.allowed.remove(messageUsername)
        chat_room.save()
        return "User has left the chatroom"
        #some logic to remove the user from the chatroom

    @database_sync_to_async
    def remove_user_chatroom(self, username, chat_room):

        User = CustomUser.objects.filter(username=username).first()
        if User:
            if username in chat_room.allowed:
                chat_room.allowed.remove(username)
                chat_room.save()
                UserLog.objects.create(user=self.scope["user"], action=f"Removed {username} from their chatroom")
                return "User Removed"
            
            else:
                return "User Doesn't Have Access"

        else:
            return "No User Found"

        # check if the user actually exists
        # add the user to the chatroom

    @database_sync_to_async
    def save_logs(self, user, message):
        UserLog.objects.create(user=user, action=message)
        

    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]
        profilePicture = event["profilePicture"]
        messageID = event["messageID"]
        notification_info = event['notification_info']

        # send the message via websocket to the frontend
        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "username": username,
                    "profilePicture": profilePicture,
                    "messageID": messageID,
                    "notification_info":notification_info
                }
            )
        )

    # save_message function that can be called to save the message to the database
    @database_sync_to_async
    def save_message(self, message,filtered_words):

        #for encryption alogrithm
        global _key_cache
        if _key_cache is None:
            
            with open("../Cryptography/chatwave.key", "rb") as key_file:
                _key_cache = key_file.read()

        cipher = Fernet(_key_cache)
        message = cipher.encrypt(message.encode()).decode()
        
        room = ChatRoom.objects.get(room_name=self.room_name)
        UserLog.objects.create(user=self.scope["user"], action=f"Sent a message to room {room} at")
        MessageObject = ChatRoomMessages.objects.create(
            room=room,
            sender=self.scope["user"],
            message=message,
            filteredWords = filtered_words
            # created = datetime.datetime.now() #not needed since models.py already handles it
        )
        return MessageObject
    

    @database_sync_to_async
    def addSong(self, song):
        isMusic = Music.objects.filter(title=song).exists()

        if isMusic:
            music = Music.objects.get(title=song)
            playlist = Playlists.objects.filter(
                user=self.scope["user"], playlist_name=music.genre
            ).first()
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
                chat_room.online_count = F("online_count") + 1
                chat_room.online_users.append(username)
            chat_room.save()

        elif status == "disconnect":
            if username in chat_room.online_users:
                chat_room.online_count = F("online_count") - 1
                chat_room.online_users.remove(username)
            chat_room.save()

        ChatRoom.objects.filter(room_name=room_name, online_count__lt=0).update(
            online_count=0
        )  # prevents the online count to drop to a negative value
