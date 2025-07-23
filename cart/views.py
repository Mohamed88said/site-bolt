from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal
from .models import Cart, CartItem
from .forms import CartLocationForm
from products.models import Product, ProductVariant

@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = CartLocationForm(request.POST, user=request.user)
        if form.is_valid():
            if form.cleaned_data['location_type'] == 'existing':
                cart.location_point = form.cleaned_data['location_id']
                cart.save()
                messages.success(request, 'Adresse de livraison mise à jour.')
            else:
                cart.location_point = None
                cart.save()
                messages.info(request, 'Veuillez saisir l\'adresse complète au moment du paiement.')
            return redirect('cart:detail')
    else:
        form = CartLocationForm(user=request.user)
    
    # Calcul de la TVA (20%) et du total final avec Decimal
    tva = cart.total_price * Decimal('0.2')
    shipping = cart.shipping_cost
    total_with_tva = cart.total_price + shipping + tva
    
    return render(request, 'cart/detail.html', {
        'cart': cart,
        'form': form,
        'tva': tva,
        'shipping': shipping,
        'estimated_delivery_time': cart.estimated_delivery_time,
        'total_with_tva': total_with_tva
    })

@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    variant_id = request.POST.get('variant_id')
    variant = None
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
    
    quantity = int(request.POST.get('quantity', 1))
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        variant=variant,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(request, f'{product.name} ajouté au panier!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_total_items': cart.total_items,
            'cart_total_price': str(cart.total_price),
            'shipping': str(cart.shipping_cost),
            'tva': str(cart.total_price * Decimal('0.2')),
            'total_with_tva': str(cart.total_price + cart.shipping_cost + (cart.total_price * Decimal('0.2')))
        })
    
    return redirect('cart:detail')

@login_required
@require_POST
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart = cart_item.cart
        return JsonResponse({
            'success': True,
            'cart_total_items': cart.total_items,
            'cart_total_price': str(cart.total_price),
            'shipping': str(cart.shipping_cost),
            'tva': str(cart.total_price * Decimal('0.2')),
            'total_with_tva': str(cart.total_price + cart.shipping_cost + (cart.total_price * Decimal('0.2')))
        })
    
    return redirect('cart:detail')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    
    messages.success(request, 'Produit retiré du panier!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart = Cart.objects.get(user=request.user)
        return JsonResponse({
            'success': True,
            'cart_total_items': cart.total_items,
            'cart_total_price': str(cart.total_price),
            'shipping': str(cart.shipping_cost),
            'tva': str(cart.total_price * Decimal('0.2')),
            'total_with_tva': str(cart.total_price + cart.shipping_cost + (cart.total_price * Decimal('0.2')))
        })
    
    return redirect('cart:detail')

@login_required
def clear_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart.clear()
    messages.success(request, 'Panier vidé!')
    return redirect('cart:detail')