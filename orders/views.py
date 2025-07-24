from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from decimal import Decimal
from .models import Order, OrderItem, OrderStatusHistory
from .forms import CheckoutForm
from cart.models import Cart
from deliveries.models import Delivery
from geolocation.models import LocationPoint
from payments.models import Payment
from notifications.models import Notification
from django.urls import reverse
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from django.utils.translation import gettext_lazy as _

@login_required
def order_tracking(request, pk):
    """Page de suivi détaillé d'une commande"""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    context = {
        'order': order,
    }
    
    return render(request, 'orders/order_tracking.html', context)
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
    slug_field = 'id'
    slug_url_kwarg = 'pk'

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
    cart = get_object_or_404(Cart, user=request.user)
    
    if not cart.items.exists():
        messages.error(request, _('Votre panier est vide.'))
        return redirect('cart:detail')
    
    # Calcul des montants
    shipping_cost = Decimal('0.00')  # Temporaire, mis à jour par le livreur
    tax_rate = Decimal('0.20')  # 20% TVA
    tax_amount = cart.total_price * tax_rate
    total_with_tax = cart.total_price + shipping_cost + tax_amount

    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                location_point = None
                if form.cleaned_data['location_type'] == 'existing':
                    try:
                        user_location = form.cleaned_data['location_id']
                        location_point = user_location.location_point
                        shipping_data = {
                            'shipping_first_name': user_location.location_point.name.split()[0] or form.cleaned_data['shipping_first_name'],
                            'shipping_last_name': ' '.join(user_location.location_point.name.split()[1:]) or form.cleaned_data['shipping_last_name'],
                            'shipping_address': user_location.location_point.address,
                            'shipping_city': user_location.location_point.city or form.cleaned_data['shipping_city'],
                            'shipping_postal_code': user_location.location_point.postal_code or form.cleaned_data['shipping_postal_code'],
                            'shipping_country': user_location.location_point.country or form.cleaned_data['shipping_country'],
                            'shipping_phone': form.cleaned_data['shipping_phone'],
                        }
                    except AttributeError:
                        messages.error(request, _('L\'adresse sélectionnée est invalide.'))
                        return redirect('orders:checkout')
                else:
                    # Géocoder l'adresse avec geopy
                    try:
                        latitude, longitude = LocationPoint.geocode_address(
                            form.cleaned_data['shipping_address'],
                            form.cleaned_data['shipping_city'],
                            form.cleaned_data['shipping_country']
                        )
                        location_point = LocationPoint.objects.create(
                            user=request.user,
                            name=f"{form.cleaned_data['shipping_first_name']} {form.cleaned_data['shipping_last_name']}",
                            address=form.cleaned_data['shipping_address'],
                            city=form.cleaned_data['shipping_city'],
                            postal_code=form.cleaned_data['shipping_postal_code'],
                            country=form.cleaned_data['shipping_country'],
                            latitude=latitude,
                            longitude=longitude
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
                    except Exception as e:
                        messages.error(request, _(f'Erreur lors du géocodage de l\'adresse : {str(e)}'))
                        return redirect('orders:checkout')
                
                # Création de la commande
                order = Order.objects.create(
                    user=request.user,
                    location_point=location_point,
                    total_amount=total_with_tax,
                    shipping_cost=shipping_cost,
                    tax_amount=tax_amount,
                    **shipping_data,
                    billing_first_name=form.cleaned_data['billing_first_name'] or shipping_data['shipping_first_name'],
                    billing_last_name=form.cleaned_data['billing_last_name'] or shipping_data['shipping_last_name'],
                    billing_address=form.cleaned_data['billing_address'] or shipping_data['shipping_address'],
                    billing_city=form.cleaned_data['billing_city'] or shipping_data['shipping_city'],
                    billing_postal_code=form.cleaned_data['billing_postal_code'] or shipping_data['shipping_postal_code'],
                    billing_country=form.cleaned_data['billing_country'] or shipping_data['shipping_country'],
                    payment_method='cash_on_delivery',
                    notes=form.cleaned_data['notes'],
                    status='pending'
                )
                
                # Création des articles de commande
                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        variant=cart_item.variant,
                        quantity=cart_item.quantity,
                        price=cart_item.price,
                        total_price=cart_item.total_price
                    )
                
                # Créer une livraison associée
                try:
                    delivery = Delivery.objects.create(
                        order=order,
                        location_point=location_point,
                        delivery_cost=shipping_cost,
                        paid_by='buyer'  # Par défaut, l'acheteur paie (modifié par le vendeur plus tard)
                    )
                except Exception as e:
                    messages.error(request, _(f'Erreur lors de la création de la livraison : {str(e)}'))
                    return redirect('orders:detail', pk=order.id)
                
                # Créer un paiement associé
                payment = Payment.objects.create(
                    order=order,
                    payment_method='cash_on_delivery',
                    amount=total_with_tax,
                    status='pending'
                )
                
                # Générer un code de confirmation et un QR code
                confirmation_code = str(uuid.uuid4()).replace('-', '')[:8]
                payment.confirmation_code = confirmation_code
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr_data = f"order:{order.id}:payment:{payment.id}:code:{confirmation_code}"
                qr.add_data(qr_data)
                qr.make(fit=True)
                qr_image = qr.make_image(fill='black', back_color='white')
                
                # Sauvegarder le QR code
                buffer = BytesIO()
                qr_image.save(buffer, format='PNG')
                filename = f'qrcode_{payment.id}.png'
                payment.qr_code_image.save(filename, File(buffer), save=True)
                buffer.close()
                payment.save()
                
                # Historique du statut
                OrderStatusHistory.objects.create(
                    order=order,
                    status='pending',
                    comment='Commande créée',
                    created_by=request.user
                )
                
                # Notification au vendeur
                for item in order.items.all():
                    Notification.objects.create(
                        user=item.product.seller,
                        title='Nouvelle commande',
                        message=f"Nouvelle commande #{str(order.id)[:8]} passée par {request.user.username}.",
                        url=reverse('orders:detail', kwargs={'pk': order.id})
                    )
                
                # Vider le panier
                cart.items.all().delete()
                
                messages.success(request, _('Votre commande a été passée avec succès !'))
                try:
                    return redirect('geolocation:delivery_person_map', delivery_id=str(delivery.id))
                except Exception as e:
                    messages.error(request, _(f'Erreur lors de la redirection vers la carte des livreurs : {str(e)}'))
                    return redirect('orders:detail', pk=order.id)
    else:
        form = CheckoutForm(user=request.user)
    
    context = {
        'form': form,
        'cart': cart,
        'shipping_cost': shipping_cost,
        'tax_rate': tax_rate,
        'tax_amount': tax_amount,
        'total_with_tax': total_with_tax
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def cancel_order(request, pk):
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
        
        messages.success(request, _('Votre commande a été annulée.'))
    else:
        messages.error(request, _('Cette commande ne peut pas être annulée.'))
    
    return redirect('orders:detail', pk=pk)

@login_required
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk, items__product__seller=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES).keys():
            order.status = new_status
            order.save()
            
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                comment=f"Statut mis à jour par {request.user.username}",
                created_by=request.user
            )
            
            messages.success(request, _("Le statut de la commande a été mis à jour."))
        else:
            messages.error(request, _("Statut invalide."))
    
    return redirect('orders:detail', pk=order.id)