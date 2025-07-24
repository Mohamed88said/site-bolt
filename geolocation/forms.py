from django import forms
from django.utils.translation import gettext_lazy as _
from .models import LocationPoint, GuineaRegion, GuineaPrefecture, GuineaCommune
from django.core.validators import MinValueValidator, MaxValueValidator

class LocationForm(forms.ModelForm):
    latitude = forms.DecimalField(
        max_digits=10,
        decimal_places=8,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        required=True,
        label=_('Latitude'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00000001'})
    )
    longitude = forms.DecimalField(
        max_digits=11,
        decimal_places=8,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        required=True,
        label=_('Longitude'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00000001'})
    )
    name = forms.CharField(
        label=_('Nom'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        required=False,
        label=_('Description'),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    region = forms.ModelChoiceField(
        queryset=GuineaRegion.objects.filter(is_active=True),
        required=False,
        label=_('Région'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    prefecture = forms.ModelChoiceField(
        queryset=GuineaPrefecture.objects.filter(is_active=True),
        required=False,
        label=_('Préfecture'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    commune = forms.ModelChoiceField(
        queryset=GuineaCommune.objects.filter(is_active=True),
        required=False,
        label=_('Commune'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    address_details = forms.CharField(
        required=False,
        label=_('Détails de l\'adresse'),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    landmark = forms.CharField(
        required=False,
        label=_('Point de repère'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    access_instructions = forms.CharField(
        required=False,
        label=_('Instructions d\'accès'),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    # Champs d'adresse standard pour compatibilité
    city = forms.CharField(
        required=False,
        label=_('Ville'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    postal_code = forms.CharField(
        required=False,
        label=_('Code postal'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    country = forms.CharField(
        required=False,
        label=_('Pays'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'value': 'Guinée'})
    )

    class Meta:
        model = LocationPoint
        fields = ['name', 'description', 'latitude', 'longitude', 'region', 'prefecture', 'commune',
                  'address_details', 'landmark', 'access_instructions', 'city', 'postal_code', 'country']

    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        prefecture = cleaned_data.get('prefecture')
        commune = cleaned_data.get('commune')

        # Validation de la hiérarchie administrative
        if commune and (not prefecture or commune.prefecture != prefecture):
            self.add_error('commune', _('La commune doit correspondre à la préfecture sélectionnée.'))
        if prefecture and (not region or prefecture.region != region):
            self.add_error('prefecture', _('La préfecture doit correspondre à la région sélectionnée.'))
        if not region and prefecture:
            self.add_error('region', _('Une région doit être sélectionnée si une préfecture est choisie.'))
        if not prefecture and commune:
            self.add_error('prefecture', _('Une préfecture doit être sélectionnée si une commune est choisie.'))

        return cleaned_data