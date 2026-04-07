from django import forms
from .models import Hostel, Block, Room


class HostelForm(forms.ModelForm):
    class Meta:
        model = Hostel
        fields = ['name', 'location', 'gender', 'image', 'price_per_semester', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'image':
                # File inputs must not get form-control — it breaks the browser picker
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['accept'] = 'image/*'
            else:
                field.widget.attrs['class'] = 'form-control'


class BlockForm(forms.ModelForm):
    class Meta:
        model = Block
        fields = ['name', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = 'form-control'


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_number', 'room_type', 'capacity', 'price_per_semester', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = 'form-control'
