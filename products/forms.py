from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from .models import Product, ProductImage, Category

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'short_description', 'category', 
            'price', 'discount_price', 'stock', 'sku', 'weight', 'dimensions',
            'seller_pays_delivery', 'delivery_included_price',
            'is_active', 'is_featured'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du produit'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Description détaillée'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description courte'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Prix en GNF'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Prix réduit (optionnel)'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantité en stock'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code produit unique'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Poids en kg'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'L x l x h en cm'}),
            'delivery_included_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Prix avec livraison'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'seller_pays_delivery': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].empty_label = "Choisir une catégorie"
        
        # Rendre certains champs obligatoires
        self.fields['name'].required = True
        self.fields['description'].required = True
        self.fields['category'].required = True
        self.fields['price'].required = True
        self.fields['stock'].required = True
        self.fields['sku'].required = True

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_main', 'order']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description de l\'image'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

ProductImageFormSet = inlineformset_factory(
    Product, 
    ProductImage, 
    form=ProductImageForm, 
    extra=3, 
    can_delete=True,
    max_num=10
)