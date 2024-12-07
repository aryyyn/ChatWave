from django.db import models
from Auth.models import CustomUser
from Chat.models import Music


class Playlists(models.Model):
    playlist_name = models.CharField(max_length=256)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="playlists")
    songs = models.TextField(blank=True)


    def __str__(self):
        return f"{self.playlist_name} - {self.user.username}"
 


