from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import MinLengthValidator, EmailValidator
import random

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given username, email, and password.
        """
        if not email:
            raise ValueError("Email address is required")
        if not username:
            raise ValueError("Username is required")
        if not password:
            raise ValueError("Password is required")

        email = self.normalize_email(email)
        
        # Validate username length
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")

        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given username, email, and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=75,
        unique=True,
        validators=[MinLengthValidator(3)],
        error_messages={
            'unique': "A user with that username already exists.",
        }
    )
    email = models.EmailField(
        max_length=256,
        unique=True,
        validators=[EmailValidator()],
        error_messages={
            'unique': "A user with that email address already exists.",
        }
    )

    def generate_verification_code():
        return random.randint(100000, 999999)

    profilePicture = models.TextField(max_length=500)
    is_verified = models.BooleanField(default=False)
    verification_code = models.IntegerField(default=generate_verification_code)

    # User status
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return True if self.is_admin else self.is_superuser

    def has_module_perms(self, app_label):
        return True if self.is_admin else self.is_superuser