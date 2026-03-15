"""
Forms for CivicPulse Grievance Portal
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Complaint, Feedback

User = get_user_model()


class RegistrationForm(UserCreationForm):
    """User registration form."""
    
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Full Name',
            'required': True
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email Address',
            'required': True
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Phone Number'
        })
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password',
            'required': True
        })
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm Password',
            'required': True
        })
    )
    
    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.name = self.cleaned_data['name']
        user.phone = self.cleaned_data.get('phone', '')
        user.role = 'citizen'  # Default role
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """User login form."""
    
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email Address',
            'required': True,
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password',
            'required': True
        })
    )


class ComplaintForm(forms.ModelForm):
    """Form for submitting complaints."""
    
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'category', 'image', 'address', 'latitude', 'longitude']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Complaint Title',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Describe your issue in detail...',
                'rows': 5,
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-file',
                'accept': 'image/*'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Location Address'
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }


class ComplaintUpdateForm(forms.ModelForm):
    """Form for officers to update complaints."""
    
    class Meta:
        model = Complaint
        fields = ['status', 'officer_remarks']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'officer_remarks': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Add remarks about the complaint...',
                'rows': 4
            })
        }


class AssignOfficerForm(forms.ModelForm):
    """Form for admin to assign officers to complaints."""
    
    class Meta:
        model = Complaint
        fields = ['assigned_officer']
        widgets = {
            'assigned_officer': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show officers in dropdown
        self.fields['assigned_officer'].queryset = User.objects.filter(role='officer')


class FeedbackForm(forms.ModelForm):
    """Form for citizen feedback after resolution."""
    
    class Meta:
        model = Feedback
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(attrs={
                'class': 'rating-radio'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Share your experience...',
                'rows': 4
            })
        }


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile."""
    
    class Meta:
        model = User
        fields = ['name', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Full Name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Phone Number'
            })
        }


class ComplaintSearchForm(forms.Form):
    """Form for searching complaints by ID."""
    
    complaint_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter Complaint ID (e.g., GRV-20240101-ABC123)'
        })
    )
