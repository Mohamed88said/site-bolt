from django import forms
from django.utils.translation import gettext_lazy as _
from geolocation.models import UserLocation

class CartLocationForm(forms.Form):
    location_type = forms.ChoiceField(
        choices=[
            ('existing', _('Utiliser une adresse enregistrée')),
            ('manual', _('Saisir une adresse manuelle (au paiement)')),
        ],
        label=_('Type d\'adresse'),
        widget=forms.RadioSelect,
        initial='existing'
    )
    
    location_id = forms.ModelChoiceField(
        queryset=UserLocation.objects.none(),
        required=False,
        label=_('Adresse enregistrée'),
        empty_label="Sélectionner une adresse"
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['location_id'].queryset = UserLocation.objects.filter(user=user)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        location_type = cleaned_data.get('location_type')
        
        if location_type == 'existing' and not cleaned_data.get('location_id'):
            self.add_error('location_id', _("Veuillez sélectionner une adresse enregistrée."))
        
        return cleaned_data