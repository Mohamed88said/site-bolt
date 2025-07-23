from django import forms
from .models import DeliveryRequest, DeliveryRating

class DeliveryRequestForm(forms.ModelForm):
    class Meta:
        model = DeliveryRequest
        fields = ['message', 'proposed_cost']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Pourquoi devrions-nous vous choisir?'}),
            'proposed_cost': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Prix proposé'}),
        }
        labels = {
            'message': 'Message',
            'proposed_cost': 'Prix proposé (€)',
        }

class DeliveryRatingForm(forms.ModelForm):
    class Meta:
        model = DeliveryRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} étoile{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Commentaire optionnel'}),
        }
        labels = {
            'rating': 'Note',
            'comment': 'Commentaire',
        }