from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError("Email is required.")
        if not username:
            raise ValueError("Username is required.")
        if not password:
            raise ValueError("Password is required.")
        
        email = self.normalize_email(email)  # Normalize email to lowercase
        user = self.model(username=username, email=email)
        user.set_password(password)  # Hash the password before saving
        user.save(using=self._db)  # Save user to database
        return user
    
    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)  # Save superuser to database
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):  # Inherit from PermissionsMixin
    username = models.CharField(max_length=75, unique=True)  # Unique username field
    email = models.EmailField(max_length=256, unique=True)  # Unique email field
    is_active = models.BooleanField(default=True)  # Field to mark if user is active
    is_admin = models.BooleanField(default=False)  # Field to mark admin status
    is_staff = models.BooleanField(default=False)  # Field to mark staff status
    is_superuser = models.BooleanField(default=False)  # Field to mark superuser status

    objects = CustomUserManager()  # Use the custom manager

    USERNAME_FIELD = 'username'  # This specifies the field used to authenticate users
    REQUIRED_FIELDS = ['email']  # This specifies fields required for creating a superuser

    def __str__(self):
        return self.username  # Display username when the user object is printed
