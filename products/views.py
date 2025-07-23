from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Avg
from .models import Product, Category, Review
from .forms import ProductForm, ProductImageFormSet, ReviewForm, ProductSearchForm
from geolocation.models import UserLocation

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).exclude(slug__isnull=True).exclude(slug='')
        form = ProductSearchForm(self.request.GET, user=self.request.user)
        if form.is_valid():
            query = form.cleaned_data.get('q')
            category = form.cleaned_data.get('category')
            min_price = form.cleaned_data.get('min_price')
            max_price = form.cleaned_data.get('max_price')
            sort_by = form.cleaned_data.get('sort', '-created_at')
            
            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query) | 
                    Q(description__icontains=query) |
                    Q(category__name__icontains=query)
                )
            if category:
                queryset = queryset.filter(category=category)
            if min_price:
                queryset = queryset.filter(price__gte=min_price)
            if max_price:
                queryset = queryset.filter(price__lte=max_price)
            if sort_by in ['price', '-price', 'name', '-name', 'created_at', '-created_at']:
                queryset = queryset.order_by(sort_by)
        
        return queryset.select_related('category', 'seller').prefetch_related('images')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['search_form'] = ProductSearchForm(self.request.GET, user=self.request.user)
        # Récupérer l'adresse principale ou celle sélectionnée dans le formulaire
        context['user_location'] = None
        if self.request.user.is_authenticated:
            form = ProductSearchForm(self.request.GET, user=self.request.user)
            if form.is_valid() and form.cleaned_data.get('location'):
                context['user_location'] = form.cleaned_data['location']
            else:
                context['user_location'] = UserLocation.objects.filter(
                    user=self.request.user, is_primary=True
                ).first()
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'
    
    def get_object(self):
        product = get_object_or_404(Product, slug=self.kwargs['slug'], is_active=True)
        product.views += 1
        product.save(update_fields=['views'])
        return product
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['reviews'] = product.reviews.all()[:10]
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        context['review_form'] = ReviewForm()
        # Récupérer l'adresse principale
        context['user_location'] = None
        if self.request.user.is_authenticated:
            context['user_location'] = UserLocation.objects.filter(
                user=self.request.user, is_primary=True
            ).first()
        return context

class CategoryListView(ListView):
    model = Product
    template_name = 'products/category.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Product.objects.filter(category=self.category, is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['user_location'] = None
        if self.request.user.is_authenticated:
            context['user_location'] = UserLocation.objects.filter(
                user=self.request.user, is_primary=True
            ).first()
        return context

class SellerProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'products/seller_products.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user).exclude(slug__isnull=True).exclude(slug='')

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_seller:
            messages.error(request, 'Vous devez être vendeur pour ajouter des produits.')
            return redirect('products:list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        response = super().form_valid(form)
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

@login_required
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
            product.rating = avg_rating or 0
            product.save()
            messages.success(request, 'Votre avis a été ajouté avec succès!')
            return redirect('products:detail', slug=slug)
    return redirect('products:detail', slug=slug)