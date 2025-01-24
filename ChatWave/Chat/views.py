from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import random
from django.contrib import messages
from django.http import JsonResponse
from django.db.models.functions import Length
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import re
import pandas as pd
from nltk.stem import WordNetLemmatizer
import keras
from keras.preprocessing.sequence import pad_sequences
from django.contrib import messages
import os
from tensorflow.keras.preprocessing.text import Tokenizer
import tensorflow as tf
import numpy as np
import json
from cryptography.fernet import Fernet


_key_cache = None 


@login_required
def deleteMessage(request, chatroom, messageid):
    if request.user.is_authenticated and not request.user.is_verified:
        return redirect("verification_logic")
    if request.method == "POST":
        try:
            message = get_object_or_404(ChatRoomMessages, id=messageid)
            if message.sender != request.user:
                return JsonResponse(
                    {"success": False, "error": "Unauthorized"}, status=403
                )
            message.isDeleted = True
            message.save()
            return JsonResponse({"success": True})
        except Exception as err:
            print(err)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


def isEligibleMethod(user, chatroom) -> bool:
    try:
        messages = (
            ChatRoomMessages.objects.filter(sender=user, room=chatroom)
            .annotate(message_length=Length("message"))
            .filter(message_length__gte=10)
        )
        unique_messages = messages.values("message").distinct()
        totalMessages = unique_messages.count()

        if totalMessages > 5:
            return True
        else:
            return False
    except Exception as err:
        print(err)


def getMessages(user, chatroom):
    messages = (
        ChatRoomMessages.objects.filter(sender=user, room=chatroom)
        .annotate(message_length=Length("message"))
        .filter(message_length__gte=10)
        .exclude(Q(message__icontains="http://") | Q(message__icontains="https://"))
        .order_by("-created")
    )

    unique_messages = messages.values("message").distinct()[:5]

    return unique_messages


def genreTest(sentiments):

    try:

        sentiment_count = {
            "sad": sentiments.count("sad"),
            "happy": sentiments.count("happy"),
            "calm": sentiments.count("calm"),
        }

        total = len(sentiments)
        predominant_sentiment = max(sentiment_count, key=sentiment_count.get)
        percentage = (sentiment_count[predominant_sentiment] / total) * 100

        if predominant_sentiment == "sad":
            if percentage > 60:
                return "Indie"
            else:
                return "Lofi"
        elif predominant_sentiment == "happy":
            if percentage > 60:
                return "Pop"
            elif percentage > 40:
                return "EDM"
            else:
                return "Hiphop"
        elif predominant_sentiment == "calm":
            if percentage > 60:
                return "Lofi"
            elif percentage > 40:
                return "Rap"
            else:
                return "Indie"

    except Exception as err:
        print(err)


def modelTest(messages):
    try:

        new_model = tf.keras.models.load_model("../Model/sentimentmodel.h5")

        try:
            with open("../Model/tokenizer.json", "r") as json_file:
                tokenizer_config = json_file.read()
                tokenizer1 = tf.keras.preprocessing.text.tokenizer_from_json(
                    tokenizer_config
                )
        except FileNotFoundError:
            raise Exception("Tokenizer file not found at '../Model/tokenizer.json'")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON format in tokenizer file")

        for resource in ["stopwords", "wordnet"]:
            try:
                nltk.download(resource, quiet=True)
            except Exception as e:
                print(f"Warning: Failed to download NLTK resource {resource}: {e}")

        stop_words = set(stopwords.words("english"))
        stemmer = SnowballStemmer("english")
        lemmatizer = WordNetLemmatizer()

        def textcleaning(text, stem=False):
            text = re.sub(
                "@\S+|https?:\S+|http?:\S|[^A-Za-z0-9]+", " ", str(text).lower()
            ).strip()

            tokens = []
            for token in text.split():
                if token not in stop_words:
                    if stem:
                        token = stemmer.stem(token)
                    if lemmatizer:
                        token = lemmatizer.lemmatize(token)
                    tokens.append(token)

            return " ".join(tokens)

        def get_sentiment(prediction):
            if 0.45 <= prediction[0] <= 0.55:
                return "calm"
            return "happy" if prediction[0] < 0.45 else "sad"

        finalResult = []
        for message in messages:
            try:
                text = message.get("message", "")
                if not text:
                    print(f"Warning: Empty message found in input")
                    continue

                cleaned_text = textcleaning(text)

                sequences = tokenizer1.texts_to_sequences([cleaned_text])
                padded_sequences = pad_sequences(sequences, padding="post", maxlen=50)

                predictions = new_model.predict(padded_sequences, verbose=0)
                sentiment = get_sentiment(predictions[0])

                finalResult.append(sentiment)

            except Exception as e:
                print(f"Error processing message: {e}")
                finalResult.append("error")

        return finalResult

    except Exception as e:
        print(f"Critical error in modelTest: {e}")
        return None


@login_required
def chatView(request, chatroom):

    if request.user.is_authenticated and not request.user.is_verified:
        return redirect("verification_logic")
    TENOR_API_KEY = settings.TENOR_API_KEY
    chat_room = get_object_or_404(ChatRoom, room_name=chatroom)

    if chat_room.category == "Other":
        if request.user.username not in chat_room.allowed:
            return redirect(chatView, chatroom="General_Chat")

    chat_messages = chat_room.chat_messages.all().order_by("created")

    # global _key_cache
    # if _key_cache is None:
    #     with open("../Cryptography/chatwave.key", "rb") as key_file:
    #         _key_cache = key_file.read()

    # cipher = Fernet(_key_cache)
    # decrypted_chat_messages = []
    # for cm in chat_messages:
    #     decrypted_chat_messages.append(cipher.decrypt(str(cm.message).encode()).decode())

    ChatRoomOther = ChatRoom.objects.filter(category="Other")
    action = request.POST.get("action")

    notifications = Notification.objects.filter(user=request.user)

    if action == "add-room":
        songs = Music.objects.all()
        randomsong = random.choice(songs)
        username = request.user.username
        ChatRoomName = f"{username}_chatroom"

        ChatRoomObject = ChatRoom.objects.filter(room_name=ChatRoomName).first()

        if not ChatRoomObject:
            ChatRoomObj = ChatRoom.objects.create(
                room_name=ChatRoomName,
                online_count=0,
                category="Other",
                allowed=[username],
            )
            return redirect(chatView, chatroom=ChatRoomName)

        else:
            return redirect(chatView, chatroom=ChatRoomName)

    elif action == "add-song":

        songs = Music.objects.all()
        randomsong = random.choice(songs)
        CRO = ChatRoom.objects.get(room_name=chatroom)

        # some logic to check whether the user has enough messages or not
        isEligible = isEligibleMethod(request.user, CRO)

        if isEligible:
            CRO = ChatRoom.objects.get(room_name=chatroom)
            messages = getMessages(request.user, CRO)
            sentiment = modelTest(messages)
            genre = str(genreTest(sentiment).lower())

            
            SentimentSong = Music.objects.filter(genre=genre)
            randomSentimentSong = random.choice(SentimentSong)
            context = {
                "chat_room": chat_room,
                "chat_messages": chat_messages,
                "songs": randomSentimentSong,
                "ChatRoomOther": ChatRoomOther,
                "songPlaying": True,
                "isEligible": isEligible,
                "TENOR_API_KEY": TENOR_API_KEY,
                "notifications": notifications,
                

            }
        else:
            context = {
                "chat_room": chat_room,
                "chat_messages": chat_messages,
                "ChatRoomOther": ChatRoomOther,
                "songPlaying": False,
                "songs": randomsong,
                "isEligible": isEligible,
                "TENOR_API_KEY": TENOR_API_KEY,
                "notifications": notifications,
                
            }
        return render(request, "chat/chat.html", context)

    songs = Music.objects.all()
    randomsong = random.choice(songs)
    
    context = {
        "chat_room": chat_room,
        "chat_messages": chat_messages,
        "ChatRoomOther": ChatRoomOther,
        "notifications": notifications,
        "TENOR_API_KEY": TENOR_API_KEY,
    }
    return render(request, "chat/chat.html", context)


@login_required
def chatHomeView(request):
    if request.user.is_authenticated and not request.user.is_verified:
        return redirect("verification_logic")

    chat_rooms = ChatRoom.objects.all()
    sum = 0
    online_users = []
    for room in chat_rooms:
        sum = sum + room.online_count
        online_users += room.online_users
    ChatRoomOther = ChatRoom.objects.filter(category="Other")
    total_online_users = sum
    context = {"total_online_users": total_online_users, "online_users": online_users, "ChatRoomOther": ChatRoomOther }

    # if request.method == "POST":
    #     action = request.POST.get('action')

    return render(request, "chat/chathome.html", context)
