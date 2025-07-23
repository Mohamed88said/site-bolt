from django import forms
from .models import ReturnRequest, ReturnItem

class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = ['reason', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Décrivez en détail le problème...'}),
        }
        labels = {
            'reason': 'Motif du retour',
            'description': 'Description détaillée',
        }

class ReturnItemForm(forms.ModelForm):
    class Meta:
        model = ReturnItem
        fields = ['quantity', 'condition']
        widgets = {
            'condition': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Décrivez l\'état du produit...'}),
        }
        labels = {
            'quantity': 'Quantité à retourner',
            'condition': 'État du produit',
        }