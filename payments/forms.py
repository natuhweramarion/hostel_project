from django import forms
from .models import Payment

class PaymentForm(forms.ModelForm):
    """Form for creating payment records"""
    
    class Meta:
        model = Payment
        fields = ['amount', 'reference_number', 'payment_method', 'academic_year', 'notes', 'receipt']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
