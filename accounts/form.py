from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Account


class RegisterForm(UserCreationForm):
    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        base_username = user.email.split('@')[0]
        username = base_username
        counter = 1
        while Account.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username
        user.save()
        return user