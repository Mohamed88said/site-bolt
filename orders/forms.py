from django import forms
from .models import Order
from geolocation.models import UserLocation
from django.utils.translation import gettext_lazy as _

class CheckoutForm(forms.Form):
    # Type de localisation
    location_type = forms.ChoiceField(choices=[
        ('existing', _('Utiliser une adresse enregistrée')),
        ('manual', _('Saisir une adresse manuelle')),
    ], label=_('Type d\'adresse'), widget=forms.RadioSelect)
    
    # Adresse enregistrée
    location_id = forms.ModelChoiceField(queryset=UserLocation.objects.none(), 
                                       required=False, label=_('Adresse enregistrée'))
    
    # Shipping address
    shipping_first_name = forms.CharField(max_length=100, label=_('Prénom'), required=False)
    shipping_last_name = forms.CharField(max_length=100, label=_('Nom'), required=False)
    shipping_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label=_('Adresse'), required=False)
    shipping_city = forms.CharField(max_length=100, label=_('Ville'), required=False)
    shipping_postal_code = forms.CharField(max_length=10, label=_('Code postal'), required=False)
    shipping_country = forms.CharField(max_length=100, label=_('Pays'), required=False)
    shipping_phone = forms.CharField(max_length=20, required=False, label=_('Téléphone'))
    
    # Billing address
    billing_first_name = forms.CharField(max_length=100, label=_('Prénom'))
    billing_last_name = forms.CharField(max_length=100, label=_('Nom'))
    billing_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label=_('Adresse'))
    billing_city = forms.CharField(max_length=100, label=_('Ville'))
    billing_postal_code = forms.CharField(max_length=10, label=_('Code postal'))
    billing_country = forms.CharField(max_length=100, label=_('Pays'))
    
    # Payment
    payment_method = forms.ChoiceField(choices=[
        ('cash_on_delivery', _('Paiement à la livraison')),
    ], label=_('Méthode de paiement'))
    
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label=_('Notes'))
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['location_id'].queryset = UserLocation.objects.filter(user=user)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        location_type = cleaned_data.get('location_type')
        
        if location_type == 'manual':
            required_fields = ['shipping_first_name', 'shipping_last_name', 'shipping_address', 
                             'shipping_city', 'shipping_postal_code', 'shipping_country']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _("Ce champ est requis pour une adresse manuelle."))
        elif location_type == 'existing' and not cleaned_data.get('location_id'):
            self.add_error('location_id', _("Veuillez sélectionner une adresse enregistrée."))
        
        return cleaned_data