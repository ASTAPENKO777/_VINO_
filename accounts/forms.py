from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile


class UserRegistrationForm(UserCreationForm):
    """Registration form with custom validation"""
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        """Ensure email is unique"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_username(self):
        """Ensure username doesn't contain special characters"""
        username = self.cleaned_data.get('username')
        if not username.isalnum():
            raise forms.ValidationError("Username must contain only letters and numbers.")
        return username


class UserProfileForm(forms.ModelForm):
    """Profile update form with validation"""
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'city', 'country', 'postal_code']

    def clean_phone_number(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone_number')
        if phone and not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone
