from django.shortcuts import render,redirect,HttpResponse
from Auth.models import *
from Chat.models import *
from Profile.models import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
import json



# def getTotalSongC
@login_required
def saveFileUrl(request, username):
    if request.method == "POST":
        if request.user.username == username:
            try:
                data = json.loads(request.body)
                image_url = data.get('image_url')
            
                user = CustomUser.objects.get(username=username)
                user.profilePicture = image_url['secure_url']
                user.save()
            except Exception as err:
                print(err)

        else:
            print("Invalid User")
            
    return render(request, 'profile.html', {'username': username})

@login_required
def profileHome(request, username):

    if request.method == "POST":
        
        currentPassword = request.POST.get("currentpassword")
        newPassword = request.POST.get("password")
        newConfirmPassword = request.POST.get("confirm-password")
        
  
        if newPassword != newConfirmPassword:
            messages.error(request, "Invalid Password")

        elif not request.user.check_password(currentPassword):
            messages.error(request, "Invalid Password")

        elif not newPassword or not currentPassword or not newConfirmPassword:
            messages.error(request, "Invalid Fields")


        else:
            request.user.set_password(newPassword)
            request.user.save()

            update_session_auth_hash(request, request.user)
            messages.success(request, "Password has been changed")
    
    userinfo = request.user
    checkusername = CustomUser.objects.filter(username=username).exists()
    

    if checkusername:
        messagecount = ChatRoomMessages.objects.filter(sender__username=username).count()
        playlists = Playlists.objects.filter(user__username= username)
        
        count = 0
        indie_song_count = 0
        pop_song_count = 0
        rap_song_count = 0
        hiphop_song_count = 0
        lofi_song_count = 0
        edm_song_count = 0
        
        for playlist in playlists:
            if playlist.songs:
                songcount = 0
                songcount += len(playlist.songs.split(','))
                count+=songcount

                if 'indie' in playlist.playlist_name:
                    indie_song_count += songcount
                elif 'pop' in playlist.playlist_name:
                    pop_song_count += songcount
                elif 'rap' in playlist.playlist_name:
                    rap_song_count += songcount
                elif 'hiphop' in playlist.playlist_name:
                    hiphop_song_count += songcount
                elif 'lofi' in playlist.playlist_name:
                    lofi_song_count += songcount
                elif 'edm' in playlist.playlist_name:
                    edm_song_count += songcount

    
        context = {
                "userinfo": CustomUser.objects.get(username=username),
                "playlists": playlists,
                "messagecount": messagecount,
                'datejoined': userinfo.date_joined,
                "songcount": count,
                "indiecount": indie_song_count,
                "popcount": pop_song_count,
                "rapcount": rap_song_count,
                "hiphopcount": hiphop_song_count,
                "loficount": lofi_song_count,
                "edmcount": edm_song_count,

            }
            
        return render(request, "profile.html", context=context)    
    
    
    else:      
        context = {
                "status": "NotFound"
            }
        return render(request, "profile.html", context=context) 
    

@login_required
def songPlayer(request, username, clickedplaylist):
    playlist = Playlists.objects.get(user__username=username, playlist_name=clickedplaylist)
    songs = playlist.songs.split(",")
    songlist = []
    for songtitle in songs:
        music = Music.objects.filter(title=songtitle).first()
        if music:
            songlist.append(music)
   
        context = {
                    "userinfo": CustomUser.objects.get(username=username),
                    "songs": songlist,

        }
    return render(request, "songplayer.html", context=context)
    
@login_required
def Player(request, username, clickedplaylist, id):
    print(username, clickedplaylist)

    playlist = Playlists.objects.get(user__username=username, playlist_name=clickedplaylist)
    songs = playlist.songs.split(",")
    songlist = []
    for songtitle in songs:
        music = Music.objects.filter(title=songtitle).first()
        if music:
            songlist.append(music)
   
       
    song = Music.objects.get(song_id=id)
    
    context = {
                    "userinfo": CustomUser.objects.get(username=username),
                    "songs": songlist,
                    "clickedsong": song

        }
    
    return render(request, "songplayer.html", context)