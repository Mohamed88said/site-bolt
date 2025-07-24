from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from .models import Product, ProductImage, Review, Category
from geolocation.models import UserLocation

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'short_description', 'category', 'price', 'discount_price', 'stock', 'sku', 'weight', 'dimensions', 'seller_pays_delivery', 'delivery_included_price', 'is_active', 'is_featured']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'short_description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'discount_price': forms.NumberInput(attrs={'step': '0.01'}),
            'delivery_included_price': forms.NumberInput(attrs={'step': '0.01'}),
            'weight': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Permettre aux vendeurs de choisir toutes les catégories actives
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].empty_label = "Choisir une catégorie"

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_main', 'order']

ProductImageFormSet = inlineformset_factory(
    Product, 
    ProductImage, 
    form=ProductImageForm, 
    extra=3, 
    can_delete=True
)

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(choices=Review.RATING_CHOICES),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

class ProductSearchForm(forms.Form):
    q = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Rechercher des produits...',
        'class': 'form-control'
    }))
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    min_price = forms.DecimalField(max_digits=10, decimal_places=2, required=False, widget=forms.NumberInput(attrs={
        'placeholder': 'Prix min',
        'class': 'form-control'
    }))
    max_price = forms.DecimalField(max_digits=10, decimal_places=2, required=False, widget=forms.NumberInput(attrs={
        'placeholder': 'Prix max',
        'class': 'form-control'
    }))
    sort = forms.ChoiceField(choices=[
        ('-created_at', 'Plus récent'),
        ('created_at', 'Plus ancien'),
        ('price', 'Prix croissant'),
        ('-price', 'Prix décroissant'),
        ('name', 'Nom A-Z'),
        ('-name', 'Nom Z-A'),
    ], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    location = forms.ModelChoiceField(
        queryset=UserLocation.objects.none(),
        required=False,
        empty_label="Sélectionner un emplacement",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        if user:
            self.fields['location'].queryset = UserLocation.objects.filter(user=user)