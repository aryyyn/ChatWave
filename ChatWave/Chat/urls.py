from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static


def redirect_to_homepage(request):
    return redirect("home/chat/")


urlpatterns = [
    path('home/chat/<str:chatroom>/', chatView, name='chatViewLogic'),
    path('home/chat/<str:chatroom>/deletemessage/<int:messageid>/', deleteMessage, name='deleteMessage'),
    path('home/chat/', chatHomeView, name='homeChatViewLogic'),
    
    path('', redirect_to_homepage, name='redirectToHomePage')

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)