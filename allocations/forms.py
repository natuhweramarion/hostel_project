from django import forms
from .models import Allocation
from django.contrib.auth import get_user_model

User = get_user_model()

class AllocationForm(forms.ModelForm):
    """Form for creating allocations"""
    
    class Meta:
        model = Allocation
        fields = ['user', 'room', 'status', 'academic_year', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # Filter users to show only students
        self.fields['user'].queryset = User.objects.filter(is_student=True)
        
        # Filter rooms to show only available ones (active allocations < capacity)
        from hostels.models import Room
        from django.db.models import Count, Q, F
        self.fields['room'].queryset = Room.objects.annotate(
            active_count=Count('allocations', filter=Q(allocations__status='active'))
        ).filter(active_count__lt=F('capacity')).select_related('block__hostel')
