from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Favorite
from products.models import Product

class FavoriteListView(LoginRequiredMixin, ListView):
    model = Favorite
    template_name = 'favorites/list.html'
    context_object_name = 'favorites'
    paginate_by = 12
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('product')

@login_required
@require_POST
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        favorite.delete()
        return JsonResponse({
            'success': True,
            'is_favorite': False,
            'message': f'{product.name} retiré des favoris!'
        })
    
    return JsonResponse({
        'success': True,
        'is_favorite': True,
        'message': f'{product.name} ajouté aux favoris!'
    })


@login_required
@require_POST
def add_to_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
    
    if created:
        message = f'{product.name} ajouté aux favoris!'
        is_favorite = True
    else:
        message = f'{product.name} est déjà dans vos favoris!'
        is_favorite = True
    
    messages.success(request, message)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_favorite': is_favorite,
            'message': message
        })
    
    return redirect('products:detail', slug=product.slug)

@login_required
@require_POST
def remove_from_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorite = get_object_or_404(Favorite, user=request.user, product=product)
    favorite.delete()
    
    message = f'{product.name} retiré des favoris!'
    messages.success(request, message)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_favorite': False,
            'message': message
        })
    
    return redirect('favorites:list')

@login_required
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    favorite = Favorite.objects.filter(user=request.user, product=product).first()
    
    if favorite:
        favorite.delete()
        is_favorite = False
        message = f'{product.name} retiré des favoris!'
    else:
        Favorite.objects.create(user=request.user, product=product)
        is_favorite = True
        message = f'{product.name} ajouté aux favoris!'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_favorite': is_favorite,
            'message': message
        })
    
    messages.success(request, message)
    return redirect('products:detail', slug=product.slug)