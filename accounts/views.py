from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg
from django.core.paginator import Paginator
from deliveries.models import Delivery, DeliveryRating
from orders.models import Order
from products.models import Product
from favorites.models import Favorite
from cart.models import Cart

from .models import User, SellerProfile, DeliveryProfile
from .forms import UserRegistrationForm, UserUpdateForm, SellerProfileForm, DeliveryProfileForm
from blog.models import BlogPost
from reviews.models import Review


@login_required
def seller_dashboard(request):
    """Tableau de bord pour les vendeurs"""
    if not request.user.is_seller:
        messages.error(request, "Vous devez être vendeur pour accéder à cette page.")
        return redirect('core:home')
    
    # Statistiques
    from django.db.models import Sum, Count, Avg
    from orders.models import OrderItem
    
    order_items = OrderItem.objects.filter(product__seller=request.user)
    
    stats = {
        'total_sales': order_items.aggregate(total=Sum('total_price'))['total'] or 0,
        'total_orders': order_items.values('order').distinct().count(),
        'total_products': request.user.products.count(),
        'average_rating': request.user.seller_profile.rating
    }
    
    # Commandes récentes
    recent_orders = Order.objects.filter(
        items__product__seller=request.user
    ).distinct().order_by('-created_at')[:10]
    
    # Livraisons en attente d'assignation
    pending_deliveries = Delivery.objects.filter(
        order__items__product__seller=request.user,
        status='pending',
        delivery_person__isnull=True
    ).distinct()[:5]
    
    # Compter les commandes par statut
    pending_orders_count = Order.objects.filter(
        items__product__seller=request.user,
        status='pending'
    ).distinct().count()
    
    processing_orders_count = Order.objects.filter(
        items__product__seller=request.user,
        status='processing'
    ).distinct().count()
    
    # Compter les livraisons actives
    active_deliveries_count = Delivery.objects.filter(
        order__items__product__seller=request.user,
        status__in=['assigned', 'in_progress']
    ).distinct().count()
    
    # Produits en rupture de stock
    low_stock_products = request.user.products.filter(
        stock__lte=5, is_active=True
    )[:5]
    
    # Compter les produits par statut
    active_products_count = request.user.products.filter(is_active=True).count()
    low_stock_count = request.user.products.filter(stock__lte=5, stock__gt=0).count()
    out_of_stock_count = request.user.products.filter(stock=0).count()
    
    # Derniers avis
    recent_reviews = Review.objects.filter(
        product__seller=request.user
    ).order_by('-created_at')[:5]
    
    return render(request, 'accounts/seller_dashboard.html', {
        'stats': stats,
        'recent_orders': recent_orders,
        'pending_deliveries': pending_deliveries,
        'pending_orders_count': pending_orders_count,
        'processing_orders_count': processing_orders_count,
        'active_deliveries_count': active_deliveries_count,
        'low_stock_products': low_stock_products,
        'active_products_count': active_products_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'recent_reviews': recent_reviews
    })


@login_required
def buyer_dashboard(request):
    """Tableau de bord pour les acheteurs"""
    if not request.user.is_buyer:
        messages.error(request, "Vous devez être acheteur pour accéder à cette page.")
        return redirect('core:home')
    
    # Statistiques client
    user_orders = Order.objects.filter(user=request.user)
    total_orders = user_orders.count()
    total_spent = user_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Favoris
    favorites_count = Favorite.objects.filter(user=request.user).count()
    
    # Panier
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = cart.total_items if cart else 0
    
    # Livraisons actives
    active_deliveries = Delivery.objects.filter(
        order__user=request.user,
        status__in=['assigned', 'in_progress']
    ).count()
    
    # Paiements en attente
    pending_payments = user_orders.filter(payment_status='pending').count()
    
    # Commandes par statut
    pending_orders = user_orders.filter(status='pending').count()
    shipped_orders = user_orders.filter(status='shipped').count()
    delivered_orders = user_orders.filter(status='delivered').count()
    
    # Commandes récentes
    recent_orders = user_orders.order_by('-created_at')[:5]
    
    # Livraisons récentes
    recent_deliveries = Delivery.objects.filter(
        order__user=request.user
    ).order_by('-created_at')[:5]
    
    return render(request, 'accounts/buyer_dashboard.html', {
        'total_orders': total_orders,
        'total_spent': total_spent,
        'favorites_count': favorites_count,
        'cart_items': cart_items,
        'active_deliveries': active_deliveries,
        'pending_payments': pending_payments,
        'pending_orders': pending_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'recent_orders': recent_orders,
        'recent_deliveries': recent_deliveries,
    })


@login_required
def delivery_dashboard(request):
    """Tableau de bord pour les livreurs"""
    if not request.user.is_delivery:
        messages.error(request, "Vous devez être livreur pour accéder à cette page.")
        return redirect('core:home')
    
    # Statistiques livreur
    user_deliveries = Delivery.objects.filter(delivery_person=request.user)
    total_deliveries = user_deliveries.count()
    completed_deliveries = user_deliveries.filter(status='completed').count()
    
    # Gains
    monthly_earnings = user_deliveries.filter(
        created_at__month=timezone.now().month,
        status='completed'
    ).aggregate(total=Sum('delivery_cost'))['total'] or 0
    
    total_earnings = user_deliveries.filter(
        status='completed'
    ).aggregate(total=Sum('delivery_cost'))['total'] or 0
    
    # Note moyenne
    ratings = DeliveryRating.objects.filter(delivery__delivery_person=request.user)
    average_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0
    total_ratings = ratings.count()
    
    # Livraisons par statut
    assigned_deliveries = user_deliveries.filter(status='assigned').count()
    in_progress_deliveries = user_deliveries.filter(status='in_progress').count()
    
    # Livraisons actuelles
    current_deliveries = user_deliveries.filter(
        status__in=['assigned', 'in_progress']
    ).order_by('-created_at')[:5]
    
    # Livraisons disponibles
    available_deliveries = Delivery.objects.filter(
        status='pending',
        delivery_person__isnull=True
    )[:5]
    available_deliveries_count = available_deliveries.count()
    
    # Performances
    success_rate = (completed_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
    
    # Dernières évaluations
    recent_ratings = ratings.order_by('-created_at')[:5]
    
    return render(request, 'accounts/delivery_dashboard.html', {
        'total_deliveries': total_deliveries,
        'completed_deliveries': completed_deliveries,
        'monthly_earnings': monthly_earnings,
        'total_earnings': total_earnings,
        'average_rating': average_rating,
        'total_ratings': total_ratings,
        'assigned_deliveries': assigned_deliveries,
        'in_progress_deliveries': in_progress_deliveries,
        'current_deliveries': current_deliveries,
        'available_deliveries': available_deliveries,
        'available_deliveries_count': available_deliveries_count,
        'success_rate': success_rate,
        'recent_ratings': recent_ratings,
    })


class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:profile')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        
        # Créer automatiquement les profils selon le type d'utilisateur
        if self.object.user_type == 'seller':
            SellerProfile.objects.create(
                user=self.object,
                company_name=f"Entreprise de {self.object.get_full_name() or self.object.username}",
                verification_status='pending'
            )
        elif self.object.user_type == 'delivery':
            DeliveryProfile.objects.create(
                user=self.object,
                verification_status='pending'
            )
        
        messages.success(self.request, 'Votre compte a été créé avec succès!')
        return response


@login_required
def profile_view(request):
    context = {'user': request.user}
    
    if request.user.is_seller:
        seller_profile, created = SellerProfile.objects.get_or_create(user=request.user)
        context['seller_profile'] = seller_profile
    elif request.user.is_delivery:
        delivery_profile, created = DeliveryProfile.objects.get_or_create(user=request.user)
        context['delivery_profile'] = delivery_profile
    
    return render(request, 'accounts/profile.html', context)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Votre profil a été mis à jour avec succès!')
        return super().form_valid(form)


@login_required
def seller_profile_update(request):
    if not request.user.is_seller:
        messages.error(request, 'Vous devez être vendeur pour accéder à cette page.')
        return redirect('accounts:profile')
    
    seller_profile = get_object_or_404(SellerProfile, user=request.user)
    
    if request.method == 'POST':
        form = SellerProfileForm(request.POST, request.FILES, instance=seller_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil vendeur a été mis à jour!')
            return redirect('accounts:profile')
    else:
        form = SellerProfileForm(instance=seller_profile)
    
    return render(request, 'accounts/seller_profile_update.html', {'form': form})


@login_required
def delivery_profile_update(request):
    if not request.user.is_delivery:
        messages.error(request, 'Vous devez être livreur pour accéder à cette page.')
        return redirect('accounts:profile')
    
    delivery_profile = get_object_or_404(DeliveryProfile, user=request.user)
    
    if request.method == 'POST':
        form = DeliveryProfileForm(request.POST, request.FILES, instance=delivery_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil livreur a été mis à jour!')
            return redirect('accounts:profile')
    else:
        form = DeliveryProfileForm(instance=delivery_profile)
    
    return render(request, 'accounts/delivery_profile_update.html', {'form': form})


def seller_profile_public(request, username):
    seller = get_object_or_404(User, username=username, user_type='seller')
    seller_profile = seller.seller_profile
    
    # Récupérer les produits actifs du vendeur
    products = Product.objects.filter(
        seller=seller, 
        is_active=True
    ).select_related('category').prefetch_related('images')
    
    # Pagination des produits
    products_paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products_page = products_paginator.get_page(page_number)
    
    # Calculer les statistiques
    orders_count = Order.objects.filter(items__product__seller=seller).distinct().count()
    
    reviews = Review.objects.filter(
        product__seller=seller
    ).select_related('user', 'product').order_by('-created_at')
    
    # Calculer la note moyenne
    rating_agg = reviews.aggregate(
        avg_rating=Avg('rating'),
        count=Count('id')
    )
    
    blog_posts = BlogPost.objects.filter(
        author=seller, 
        status='published'
    ).order_by('-published_at')[:3]
    
    context = {
        'seller': seller,
        'seller_profile': seller_profile,
        'products': products_page,
        'products_count': products.count(),
        'orders_count': orders_count,
        'reviews': reviews[:5],
        'reviews_count': rating_agg['count'],
        'rating_avg': round(rating_agg['avg_rating'] or 0, 2),
        'blog_posts': blog_posts,
        'blog_posts_count': blog_posts.count(),
    }
    
    return render(request, 'accounts/seller_profile_public.html', context)