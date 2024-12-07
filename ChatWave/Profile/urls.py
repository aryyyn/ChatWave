from django.urls import path
from .views import *

urlpatterns = [
    path('account/<str:username>', profileHome, name="profile")
]
