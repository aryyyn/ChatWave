from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import datetime
from django.utils.timezone import now
import syncedlyrics
import re
import json


# Create your models here.
class ChatRoom(models.Model):
    room_name = models.CharField(max_length=100, unique=True)
    online_count = models.IntegerField(blank=True)
    online_users = models.JSONField(default=list, blank=True)
    category = models.CharField(max_length=100, default="General")
    allowed = models.JSONField(default=list, blank=True)


    def __str__(self):
        return self.room_name
    

class ChatRoomMessages(models.Model):
    room = models.ForeignKey(ChatRoom, related_name="chat_messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.CharField(max_length=500)
    created = models.DateTimeField(default=now)
    isDeleted = models.BooleanField(default=False)
    filteredWords = models.TextField(blank=True)


    def __str__(self):
        return f'{self.room} : {self.sender.username} : {self.message}'
    

    class Meta:
        ordering = ['-created']


class Music(models.Model):
    song_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=256)
    genre = models.CharField(max_length=100)
    artist = models.CharField(max_length=100)
    thumbnail = models.ImageField(upload_to='thumbnails/')
    song = models.FileField(upload_to='songs/')
    lyrics = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.lyrics:
            try:
                query = self.title
                lrc = syncedlyrics.search(query)

                lines = lrc.split("\n")
                json_data = []
                pattern = r"\[(\d+:\d+\.\d+)\] (.+)"
                for line in lines:
                    match = re.match(pattern, line)
                    if match:
                        timestamp, text = match.groups()
                        text = bytes(text, "utf-8").decode("unicode_escape")
                        json_entry = {"time": timestamp, "lyrics": text}
                        json_data.append(json_entry)

                self.lyrics = json.dumps(json_data, indent=4)
            except Exception as e:
                print(f"Error fetching lyrics: {e}")
                self.lyrics = None
        super().save(*args, **kwargs)
    

    def __str__(self):
        return f"{self.title} by {self.artist}"



class Notification(models.Model):
    notification_text = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.notification_text
    
