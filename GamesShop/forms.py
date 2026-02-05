import os.path

from transliterate import translit, exceptions
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation.reloader import translation_file_changed
from django.utils.text import slugify
from .models import CustomUser, Game
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm
class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')

    def clean_password2(self):

        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
class LoginForm(forms.Form):
    email=forms.EmailField(
        label='Email address',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'})
    )
    password=forms.CharField(
        label='password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '*******'})
    )
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields=['email', 'first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'email': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Почта'}),
        }
class PasswordChangeForm(BasePasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Текущий пароль'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Новый пароль'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Подтвердите новый пароль'
        })
class GameAddForm(forms.ModelForm):
    class Meta:
        model=Game
        fields = ['title', 'genre', 'image', 'developer', 'description', 'price', 'is_active']

        def save(self, commit=True):
            instance = super().save(commit=False)
            image = self.cleaned_data.get('image')

            if image:
                base_name, ext = os.path.splitext(image.name)
                try:
                    translit_name = translit(base_name, reversed=True)
                except exceptions.TransliterationError:
                    translit_name = base_name

                safe_name = f"{slugify(translit_name)}{ext}"
                instance.image.name = os.path.join('games', safe_name)
            return instance

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'genre': forms.TextInput(attrs={'class': 'form-control'}),
            'developer': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }