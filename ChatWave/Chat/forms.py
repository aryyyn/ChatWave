from django.forms import ModelForm
from django import forms
from .models import *


class ChatMessagesForm(ModelForm):
    class Meta:
        model = ChatRoomMessages
        fields = ['message']
        widgets = {
            'message': forms.TextInput(attrs={'placeholder': 'Chat here..', 'class': 'p-2 text black',  'maxlength': '250', 'autocomplete':"off", 'autofocus': True})
        }