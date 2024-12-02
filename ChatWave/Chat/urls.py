from django.urls import path
from .views import *

urlpatterns = [
    path('chat/<str:chatroom>/', chatView, name='chatViewLogic'),
    path('chat/', chatHomeView, name='homeChatViewLogic')

]