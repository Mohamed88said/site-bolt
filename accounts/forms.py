from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, SellerProfile, DeliveryProfile

class UserRegistrationForm(UserCreationForm):
    # Limiter les choix aux rôles autorisés à l'inscription
    ALLOWED_USER_TYPES = [
        ('buyer', 'Acheteur'),
        ('seller', 'Vendeur'),
        ('delivery', 'Livreur'),
    ]
    
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=ALLOWED_USER_TYPES, required=True)
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    city = forms.CharField(max_length=100, required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre l'adresse obligatoire pour les vendeurs
        if self.data.get('user_type') == 'seller':
            self.fields['address'].required = True
            self.fields['city'].required = True
    
    class Meta:
        model = User
        fields = ('username', 'email', 'user_type', 'phone', 'address', 'city', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.user_type = self.cleaned_data['user_type']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        user.city = self.cleaned_data['city']
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'address', 'city', 'postal_code', 'country', 'avatar', 'birth_date')
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        fields = (
            'company_name', 'company_description', 'logo', 'website', 'tax_number', 'bank_account',
            'identity_document', 'rccm_document', 'business_license',
            'accepts_cash_on_delivery', 'accepts_store_pickup'
        )
        widgets = {
            'company_description': forms.Textarea(attrs={'rows': 4}),
        }

class DeliveryProfileForm(forms.ModelForm):
    class Meta:
        model = DeliveryProfile
        fields = (
            'vehicle_type', 'license_plate', 'license_number', 'availability_radius', 'is_available',
            'license_document', 'vehicle_registration', 'insurance_document'
        )
        widgets = {
            'availability_radius': forms.NumberInput(attrs={'min': 1, 'max': 100}),
        }