from django.urls import path
from .views import *


def redirect_to_homepage(request):
    return redirect("home/chat/")


urlpatterns = [
    path('home/chat/<str:chatroom>/', chatView, name='chatViewLogic'),
    path('home/chat/', chatHomeView, name='homeChatViewLogic'),
    path('', redirect_to_homepage, name='redirectToHomePage')

]