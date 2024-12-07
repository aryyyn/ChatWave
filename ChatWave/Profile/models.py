from django.db import models
from Auth.models import CustomUser
from Chat.models import Music

class Playlist(models.Model):
    playlist_id = models.IntegerField(primary_key=True)
    playlist_name = models.CharField(max_length=256)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="playlists")
    songs = models.ManyToManyField(Music, related_name="playlists")


    def __str__(self):
        return f"{self.playlist_name} - {self.user.username}"
 


