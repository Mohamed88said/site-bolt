from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.urls import reverse
from decimal import Decimal
import uuid
import qrcode
from io import BytesIO
from django.core.files import File

from .models import Order, OrderItem, OrderStatusHistory
from .forms import CheckoutForm
from cart.models import Cart
from deliveries.models import Delivery
from payments.models import Payment
from notifications.models import Notification
from geolocation.models import LocationPoint

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/list.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        if self.request.user.is_seller:
            return Order.objects.filter(
                items__product__seller=self.request.user
            ).distinct().order_by('-created_at')
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        if self.request.user.is_seller:
            return Order.objects.filter(items__product__seller=self.request.user)
        return Order.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        
        if self.request.user.is_seller:
            context['seller_items'] = order.items.filter(product__seller=self.request.user)
            context['is_seller_view'] = True
        else:
            context['is_seller_view'] = False
        
        return context

@login_required
def checkout(request):
    """Processus de commande"""
    cart = get_object_or_404(Cart, user=request.user)
    
    if not cart.items.exists():
        messages.error(request, 'Votre panier est vide.')
        return redirect('cart:detail')
    
    # Calculs
    tax_rate = Decimal('0.20')  # 20% TVA
    tax_amount = cart.total_price * tax_rate
    
    # Frais de livraison temporaires (sera mis à jour par le livreur)
    shipping_cost = Decimal('0.00')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                # Préparer les données d'adresse
                location_point = None
                
                if form.cleaned_data['location_type'] == 'existing':
                    user_location = form.cleaned_data['location_id']
                    location_point = user_location.location_point
                    shipping_data = {
                        'shipping_first_name': user_location.location_point.name.split()[0] if user_location.location_point.name else 'Client',
                        'shipping_last_name': ' '.join(user_location.location_point.name.split()[1:]) if len(user_location.location_point.name.split()) > 1 else '',
                        'shipping_address': user_location.location_point.address or user_location.location_point.description,
                        'shipping_city': user_location.location_point.city or 'Conakry',
                        'shipping_postal_code': user_location.location_point.postal_code or '00000',
                        'shipping_country': user_location.location_point.country or 'Guinée',
                        'shipping_phone': form.cleaned_data.get('shipping_phone', ''),
                    }
                else:
                    # Créer un nouveau point de localisation
                    location_point = LocationPoint.objects.create(
                        user=request.user,
                        name=f"{form.cleaned_data['shipping_first_name']} {form.cleaned_data['shipping_last_name']}",
                        address=form.cleaned_data['shipping_address'],
                        city=form.cleaned_data['shipping_city'],
                        postal_code=form.cleaned_data['shipping_postal_code'],
                        country=form.cleaned_data['shipping_country'],
                        latitude=9.6412,  # Coordonnées par défaut (Conakry)
                        longitude=-13.5784,
                        description=form.cleaned_data['shipping_address']
                    )
                    shipping_data = {
                        'shipping_first_name': form.cleaned_data['shipping_first_name'],
                        'shipping_last_name': form.cleaned_data['shipping_last_name'],
                        'shipping_address': form.cleaned_data['shipping_address'],
                        'shipping_city': form.cleaned_data['shipping_city'],
                        'shipping_postal_code': form.cleaned_data['shipping_postal_code'],
                        'shipping_country': form.cleaned_data['shipping_country'],
                        'shipping_phone': form.cleaned_data['shipping_phone'],
                    }
                
                # Créer la commande
                order = Order.objects.create(
                    user=request.user,
                    location_point=location_point,
                    total_amount=cart.total_price,
                    shipping_cost=shipping_cost,
                    tax_amount=tax_amount,
                    **shipping_data,
                    billing_first_name=form.cleaned_data['billing_first_name'],
                    billing_last_name=form.cleaned_data['billing_last_name'],
                    billing_address=form.cleaned_data['billing_address'],
                    billing_city=form.cleaned_data['billing_city'],
                    billing_postal_code=form.cleaned_data['billing_postal_code'],
                    billing_country=form.cleaned_data['billing_country'],
                    payment_method='cash_on_delivery',
                    notes=form.cleaned_data['notes'],
                    status='pending'
                )
                
                # Créer les articles de commande
                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        variant=cart_item.variant,
                        quantity=cart_item.quantity,
                        price=cart_item.price,
                        total_price=cart_item.total_price
                    )
                
                # Créer la livraison
                delivery = Delivery.objects.create(
                    order=order,
                    location_point=location_point,
                    delivery_cost=15000,  # 15,000 GNF par défaut
                    paid_by='buyer'  # Par défaut, modifiable par le vendeur
                )
                
                # Créer le paiement avec QR code
                payment = Payment.objects.create(
                    order=order,
                    payment_method='cash_on_delivery',
                    amount=order.total_with_shipping,
                    status='pending'
                )
                
                # Générer QR code
                confirmation_code = str(uuid.uuid4()).replace('-', '')[:6].upper()
                payment.confirmation_code = confirmation_code
                
                qr_data = f"ORDER:{order.id}|PAYMENT:{payment.id}|CODE:{confirmation_code}|AMOUNT:{payment.amount}"
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(qr_data)
                qr.make(fit=True)
                qr_image = qr.make_image(fill='black', back_color='white')
                
                buffer = BytesIO()
                qr_image.save(buffer, format='PNG')
                filename = f'qrcode_{payment.id}.png'
                payment.qr_code_image.save(filename, File(buffer), save=True)
                buffer.close()
                payment.save()
                
                # Historique
                OrderStatusHistory.objects.create(
                    order=order,
                    status='pending',
                    comment='Commande créée',
                    created_by=request.user
                )
                
                # Notifications aux vendeurs
                sellers = set()
                for item in order.items.all():
                    sellers.add(item.product.seller)
                
                for seller in sellers:
                    Notification.objects.create(
                        user=seller,
                        title='Nouvelle commande',
                        message=f"Nouvelle commande #{str(order.id)[:8]} de {request.user.username}",
                        notification_type='order_placed',
                        url=reverse('orders:detail', kwargs={'pk': order.id})
                    )
                
                # Vider le panier
                cart.items.all().delete()
                
                messages.success(request, 'Votre commande a été passée avec succès!')
                return redirect('orders:detail', pk=order.id)
    else:
        form = CheckoutForm(user=request.user)
    
    context = {
        'form': form,
        'cart': cart,
        'tax_amount': tax_amount,
        'total_with_tax': cart.total_price + tax_amount,
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def cancel_order(request, pk):
    """Annuler une commande"""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    if order.can_be_cancelled:
        order.status = 'cancelled'
        order.save()
        
        OrderStatusHistory.objects.create(
            order=order,
            status='cancelled',
            comment='Commande annulée par le client',
            created_by=request.user
        )
        
        messages.success(request, 'Votre commande a été annulée.')
    else:
        messages.error(request, 'Cette commande ne peut pas être annulée.')
    
    return redirect('orders:detail', pk=pk)

@login_required
def update_order_status(request, pk):
    """Mettre à jour le statut d'une commande (vendeur)"""
    order = get_object_or_404(Order, pk=pk, items__product__seller=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES).keys():
            old_status = order.status
            order.status = new_status
            order.save()
            
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                comment=f"Statut mis à jour de '{old_status}' vers '{new_status}' par {request.user.username}",
                created_by=request.user
            )
            
            # Notification à l'acheteur
            Notification.objects.create(
                user=order.user,
                title='Statut de commande mis à jour',
                message=f"Votre commande #{str(order.id)[:8]} est maintenant '{order.get_status_display()}'",
                notification_type='order_confirmed',
                url=reverse('orders:detail', kwargs={'pk': order.id})
            )
            
            messages.success(request, "Le statut de la commande a été mis à jour.")
        else:
            messages.error(request, "Statut invalide.")
    
    return redirect('orders:detail', pk=order.id)