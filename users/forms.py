from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile details (not password)."""
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number',
                  'department', 'level', 'date_of_birth', 'photo']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'photo': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'photo':
                field.widget.attrs['class'] = 'form-control'


class StudentRegistrationForm(UserCreationForm):
    """Form for student registration"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'student_id', 
                  'department', 'level', 'phone_number', 'gender', 'date_of_birth', 
                  'password1', 'password2']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field.required:
                field.widget.attrs['required'] = 'required'
