from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from .models import Product, Category
from .forms import ProductForm, ProductImageFormSet
from reviews.models import Review

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True, is_visible=True).select_related('category', 'seller').prefetch_related('images')
        
        # Filtres
        query = self.request.GET.get('q')
        category_slug = self.request.GET.get('category')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        sort_by = self.request.GET.get('sort', '-created_at')
        
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            )
        
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass
        
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        valid_sorts = ['price', '-price', 'name', '-name', 'created_at', '-created_at', 'rating', '-rating']
        if sort_by in valid_sorts:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['current_query'] = self.request.GET.get('q', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True, is_visible=True)
    
    def get_object(self):
        product = get_object_or_404(self.get_queryset(), slug=self.kwargs['slug'])
        # Incrémenter les vues
        product.views += 1
        product.save(update_fields=['views'])
        return product
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Produits similaires
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True,
            is_visible=True
        ).exclude(id=product.id)[:4]
        
        # Avis
        context['reviews'] = product.reviews.filter(is_active=True, is_approved=True).select_related('user')[:10]
        
        return context

class CategoryListView(ListView):
    model = Product
    template_name = 'products/category.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'], is_active=True)
        return Product.objects.filter(
            category=self.category, 
            is_active=True,
            is_visible=True
        ).select_related('seller').prefetch_related('images')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

class SellerProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'products/seller_products.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_seller:
            messages.error(request, 'Vous devez être vendeur pour accéder à cette page.')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user).order_by('-created_at')

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_seller:
            messages.error(request, 'Vous devez être vendeur pour ajouter des produits.')
            return redirect('products:list')
        
        # Vérifier si le vendeur est vérifié
        if not hasattr(request.user, 'seller_profile') or not request.user.seller_profile.is_verified:
            messages.warning(request, 'Votre profil vendeur doit être vérifié pour ajouter des produits.')
            return redirect('accounts:seller_profile_update')
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        response = super().form_valid(form)
        
        # Traiter les images
        formset = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if formset.is_valid():
            formset.save()
        
        messages.success(self.request, 'Produit ajouté avec succès!')
        return redirect('products:seller_products')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProductImageFormSet(self.request.POST, self.request.FILES)
        else:
            context['formset'] = ProductImageFormSet()
        return context

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    
    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Traiter les images
        formset = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if formset.is_valid():
            formset.save()
        
        messages.success(self.request, 'Produit mis à jour avec succès!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['formset'] = ProductImageFormSet(instance=self.object)
        return context

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'products/product_confirm_delete.html'
    success_url = reverse_lazy('products:seller_products')
    
    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Produit supprimé avec succès!')
        return super().delete(request, *args, **kwargs)

@login_required
def add_review(request, slug):
    """Ajouter un avis sur un produit"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Vérifier si l'utilisateur a déjà laissé un avis
    if Review.objects.filter(product=product, user=request.user).exists():
        messages.error(request, 'Vous avez déjà laissé un avis pour ce produit.')
        return redirect('products:detail', slug=slug)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title', '')
        comment = request.POST.get('comment', '')
        
        if rating:
            # Vérifier si l'utilisateur a acheté ce produit
            order = None
            if request.user.orders.filter(items__product=product, status='delivered').exists():
                order = request.user.orders.filter(items__product=product, status='delivered').first()
            
            Review.objects.create(
                product=product,
                user=request.user,
                order=order,
                rating=int(rating),
                title=title,
                comment=comment,
                is_verified=bool(order)
            )
            
            messages.success(request, 'Votre avis a été ajouté avec succès!')
        else:
            messages.error(request, 'Veuillez donner une note.')
    
    return redirect('products:detail', slug=slug)