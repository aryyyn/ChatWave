from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import datetime
from django.utils.timezone import now


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
    message = models.CharField(max_length=250)
    created = models.DateTimeField(default=now)
    isDeleted = models.BooleanField(default=False)


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
    

    def __str__(self):
        return f"{self.title} by {self.artist}"



class Notification(models.Model):
    notification_text = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.notification_text
    
