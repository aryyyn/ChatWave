from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
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


def isEligibleMethod(user, chatroom) -> bool:
    try:
        messages = ChatRoomMessages.objects.filter(
        sender=user,
        room=chatroom
            ).annotate(
                message_length=Length('message')
            ).filter(
                message_length__gte=10
            )
        unique_messages = messages.values('message').distinct()
        totalMessages = unique_messages.count()

        if totalMessages > 5:
            return True
        else:
            return False
    except Exception as err:
        print(err)

def getMessages(user, chatroom):
    messages = ChatRoomMessages.objects.filter(
        sender=user,
        room=chatroom
    ).annotate(
        message_length=Length('message')
    ).filter(
        message_length__gte=10
    ).order_by('-created')

    # Perform `distinct` before slicing
    unique_messages = messages.values('message').distinct()[:5]

    return unique_messages

def genreTest(sentiments):

    sentiment_count = {"sad": sentiments.count("sad"),
                       "happy": sentiments.count("happy"),
                       "calm": sentiments.count("calm")}
    

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



def modelTest(messages):
    # model_path = os.path.abspath('../../model/sentimentmodel.h5')
    # print(model_path)
    new_model = tf.keras.models.load_model('../Model/sentimentmodel.h5')
    with open('../Model/tokenizer.json') as json_file:
        json_string = json_file.read()

    tokenizer1 = tf.keras.preprocessing.text.tokenizer_from_json(json_string)
    tokenizer1.oov_token = '<UNK>'

    nltk.download('stopwords')
    nltk.download('wordnet')
    stop_words = stopwords.words('english')
    stemmer = SnowballStemmer('english')
    lemmatizer = WordNetLemmatizer()


    text_cleaning_re = "@\S+|https?:\S+|http?:\S|[^A-Za-z0-9]+"

    def textcleaning(text, stem=False):
        tokens = []
        text = re.sub(text_cleaning_re, ' ', str(text)).strip()
        
        for token in text.split():
            if token not in stop_words:
                if stem:
                    tokens.append(stemmer.stem(token))
                if lemmatizer:
                    tokens.append(lemmatizer.lemmatize(token))
                else:
                    tokens.append(token)
                    
                    
        return " ".join(tokens)
    finalResult = []
    for message in messages:
        print(message)
        text = message['message']
        words_to_check = ["I", "IT","it", "you", "he", "she", "they", "we", "The", 'the', "I've", "this", "This", "i", "I'm", "It", 'it', "It's" ,"it's" , "how", "How", "Memories", "memories"]  

        words_in_text = text.split()
        filtered_words = [word for word in words_in_text if word not in words_to_check]
        new_text = " ".join(filtered_words)
        text = new_text
        list(text)
        text = textcleaning(text)
        
        tokenizer1.fit_on_texts([text])

        sequences = tokenizer1.texts_to_sequences([text])
        sequences = pad_sequences(sequences, padding='post', maxlen=50)

        predictions = new_model.predict(sequences)

        predictions.tolist

        result = ""
        if (predictions[0][0] > 0.45 and predictions[0][0] < 0.55):
            result = "calm"
        else:
            index = np.argmax(predictions)
            if (index == 0):
                result = "sad"
            else:
                result = "happy"
    
        finalResult.append(result)

    return finalResult

@login_required
def chatView(request, chatroom):


    TENOR_API_KEY = settings.TENOR_API_KEY
    chat_room = get_object_or_404(ChatRoom, room_name=chatroom)

    if chat_room.category == "Other": 
        if request.user.username not in chat_room.allowed:
            return redirect(chatView, chatroom="General_Chat")

    
    chat_messages = chat_room.chat_messages.all().order_by("created")
    ChatRoomOther = ChatRoom.objects.filter(category="Other")
    action = request.POST.get("action")
    notifications = Notification.objects.filter(user = request.user)
    



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

    elif action == "add-song":
        
        songs = Music.objects.all()
        randomsong = random.choice(songs)
        CRO = ChatRoom.objects.get(room_name = chatroom)

        #some logic to check whether the user has enough messages or not
        isEligible = isEligibleMethod(request.user,CRO)


        
        if (isEligible):
            CRO = ChatRoom.objects.get(room_name = chatroom)
            messages = getMessages(request.user,CRO)
            sentiment = modelTest(messages)
            genre = genreTest(  sentiment).lower()
            print(genre)

            SentimentSong = Music.objects.filter(genre=genre)
            randomSentimentSong = random.choice(SentimentSong)
            context = {
                "chat_room": chat_room,
                "chat_messages": chat_messages,
                "songs": randomSentimentSong,
                "ChatRoomOther": ChatRoomOther,
                "songPlaying": True,
                "isEligible": isEligible,
                "TENOR_API_KEY": TENOR_API_KEY
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
