from django.urls import path
from .views import *

urlpatterns = [
    path('chat/', chatView, name='chatViewLogic'),

]