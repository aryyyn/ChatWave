from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('account/<str:username>/', profileHome, name="profile"),
    path('account/<str:username>/player/<str:clickedplaylist>/', songPlayer, name="songPlayer"),
    path('account/<str:username>/player/<str:clickedplaylist>/<int:id>/', Player, name="Player")
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)