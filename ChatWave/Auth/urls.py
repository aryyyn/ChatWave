from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterLogic, name='register_logic'),
    path('login/', loginLogic, name='login_logic'),  
    path('logout/', logoutLogic, name="logout_logic"),
    path('verification', verificationLogic, name='verification_logic'),
    path('forgot_password', forgotPassword, name='forgot_password'),
    path('new_password', newPassword, name="new_password")
]