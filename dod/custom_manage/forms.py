
from django import forms

from accounts.models import User


class PostForm(forms.Form):
    phone = forms.CharField()
    password = forms.CharField()


