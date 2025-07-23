from django.shortcuts import render
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import Http404
from products.models import Product, Category
from analytics.models import SearchQuery, ProductView
from .models import FAQ, ContactMessage
from .forms import ContactForm
from orders.models import Order
from django.contrib.auth import get_user_model
from reviews.models import Review
from django.contrib import messages
from django.shortcuts import redirect

User = get_user_model()

def get_client_ip(request):
    """Get client IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def home(request):
    """Home page view."""
    # Get featured products
    featured_products = Product.objects.filter(
        is_featured=True, 
        is_active=True,
        slug__isnull=False  # Ajout pour éviter les produits sans slug
    ).select_related('category', 'seller').prefetch_related('images', 'reviews')[:8]
    
    # Get new products
    new_products = Product.objects.filter(
        is_active=True,
        slug__isnull=False  # Ajout pour éviter les produits sans slug
    ).select_related('category', 'seller').prefetch_related('images').order_by('-created_at')[:8]
    
    # Get categories with product count
    categories = Category.objects.filter(
        is_active=True, 
        parent=None
    ).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )[:8]
    
    # Calculate dynamic stats
    product_count = Product.objects.filter(is_active=True).count()
    satisfied_customers = Order.objects.values('user').distinct().count()  # Approximation
    seller_count = User.objects.filter(seller_profile__isnull=False).count()  # Basé sur seller_profile
    
    # Get recent reviews
    recent_reviews = Review.objects.filter(is_active=True).select_related('user', 'product').order_by('-created_at')[:3]
    
    context = {
        'featured_products': featured_products,
        'new_products': new_products,
        'categories': categories,
        'product_count': product_count,
        'satisfied_customers': satisfied_customers,
        'seller_count': seller_count,
        'recent_reviews': recent_reviews,
    }
    
    return render(request, 'core/home.html', context)

def search(request):
    """Search products view."""
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', '-created_at')
    
    results = Product.objects.filter(is_active=True)
    
    # Apply search query
    if query:
        results = results.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(seller__username__icontains=query)
        )
        
        # Log search query
        SearchQuery.objects.create(
            query=query,
            user=request.user if request.user.is_authenticated else None,
            results_count=results.count(),
            ip_address=get_client_ip(request)
        )
    
    # Apply category filter
    if category_slug:
        results = results.filter(category__slug=category_slug)
    
    # Apply price filters
    if min_price:
        try:
            min_price = float(min_price)
            results = results.filter(price__gte=min_price)
        except ValueError:
            pass
    
    if max_price:
        try:
            max_price = float(max_price)
            results = results.filter(price__lte=max_price)
        except ValueError:
            pass
    
    # Apply sorting
    valid_sorts = ['price', '-price', 'name', '-name', 'created_at', '-created_at', 'rating', '-rating']
    if sort_by in valid_sorts:
        results = results.order_by(sort_by)
    else:
        results = results.order_by('-created_at')
    
    # Select related and prefetch related for performance
    results = results.select_related('category', 'seller').prefetch_related('images', 'reviews')
    
    # Pagination
    paginator = Paginator(results, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'query': query,
        'results': page_obj,
        'categories': categories,
        'total_results': results.count(),
        'current_category': category_slug,
        'current_min_price': min_price,
        'current_max_price': max_price,
        'current_sort': sort_by,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'core/search.html', context)

def contact(request):
    """Contact page view."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre message a été envoyé avec succès! Nous vous répondrons dans les plus brefs délais.')
            return redirect('core:contact')
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {'form': form})

def faq(request):
    """FAQ page view."""
    faqs = FAQ.objects.filter(is_active=True)
    
    # Grouper les FAQ par catégorie
    faq_by_category = {}
    for faq in faqs:
        if faq.category not in faq_by_category:
            faq_by_category[faq.category] = []
        faq_by_category[faq.category].append(faq)
    
    return render(request, 'core/faq.html', {'faq_by_category': faq_by_category})

def mentions_legales(request):
    """Mentions légales page."""
    return render(request, 'core/mentions_legales.html')

def conditions(request):
    """Conditions d'utilisation page."""
    return render(request, 'core/conditions.html')

def politique_retour(request):
    """Politique de retour page."""
    return render(request, 'core/politique_retour.html')

def about(request):
    """About page view."""
    return render(request, 'core/about.html')

def privacy(request):
    """Privacy policy page."""
    return render(request, 'core/privacy.html')

def handler404(request, exception):
    """Custom 404 error page."""
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """Custom 500 error page."""
    return render(request, 'errors/500.html', status=500)