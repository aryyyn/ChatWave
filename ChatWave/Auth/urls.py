from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterLogic, name='register_logic'),
    path('login/', loginLogic, name='login_logic'),  
    path('logout/', logoutLogic, name="logout_logic")
]