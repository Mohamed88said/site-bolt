from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .models import Payment
from orders.models import Order
import json

@login_required
def qr_scan_payment(request, payment_id):
    """Page de paiement après scan du QR code"""
    payment = get_object_or_404(Payment, id=payment_id)
    order = payment.order
    delivery = getattr(order, 'delivery', None)
    
    if payment.status == 'completed':
        return render(request, 'payments/already_paid.html', {'payment': payment})
    
    context = {
        'payment': payment,
        'order': order,
        'delivery': delivery,
        'total_amount': payment.amount,
    }
    
    return render(request, 'payments/qr_scan_payment.html', context)

@login_required
def process_payment(request, payment_id):
    """Traiter le paiement après sélection de la méthode"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        confirmation_code = request.POST.get('confirmation_code')
        
        # Vérifier le code de confirmation
        if confirmation_code != payment.confirmation_code:
            return JsonResponse({'success': False, 'error': 'Code de confirmation incorrect'})
        
        # Traiter selon la méthode
        if payment_method == 'cash':
            payment.payment_method = 'cash_on_delivery'
            payment.status = 'completed'
            payment.confirmed_at = timezone.now()
            payment.save()
            
            # Mettre à jour la commande
            payment.order.payment_status = 'completed'
            payment.order.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Paiement en espèces confirmé',
                'redirect_url': reverse('orders:detail', kwargs={'pk': payment.order.id})
            })
        
        elif payment_method in ['stripe', 'paypal', 'mobile_money']:
            # Pour les autres méthodes, rediriger vers le processeur approprié
            payment.payment_method = payment_method
            payment.save()
            
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('payments:process_' + payment_method, kwargs={'payment_id': payment.id})
            })
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@login_required
def process_stripe(request, payment_id):
    """Traiter un paiement Stripe"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Ici vous intégreriez Stripe
    # Pour l'instant, on simule un paiement réussi
    payment.status = 'completed'
    payment.confirmed_at = timezone.now()
    payment.save()
    
    payment.order.payment_status = 'completed'
    payment.order.save()
    
    messages.success(request, 'Paiement par carte réussi.')
    return redirect('orders:detail', pk=payment.order.id)

@login_required
def process_paypal(request, payment_id):
    """Traiter un paiement PayPal"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Ici vous intégreriez PayPal
    # Pour l'instant, on simule un paiement réussi
    payment.status = 'completed'
    payment.confirmed_at = timezone.now()
    payment.save()
    
    payment.order.payment_status = 'completed'
    payment.order.save()
    
    messages.success(request, 'Paiement PayPal réussi.')
    return redirect('orders:detail', pk=payment.order.id)

@login_required
def process_mobile_money(request, payment_id):
    """Traiter un paiement Mobile Money"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        provider = request.POST.get('provider')
        
        if not phone_number or not provider:
            messages.error(request, 'Numéro de téléphone et fournisseur requis.')
            return redirect('payments:qr_scan', payment_id=payment_id)
        
        # Sauvegarder les infos Mobile Money
        payment.mobile_money_phone = phone_number
        payment.mobile_money_provider = provider
        payment.status = 'completed'  # Simulation
        payment.confirmed_at = timezone.now()
        payment.save()
        
        payment.order.payment_status = 'completed'
        payment.order.save()
        
        messages.success(request, f'Paiement {provider} Money réussi.')
        return redirect('orders:detail', pk=payment.order.id)
    
    return render(request, 'payments/mobile_money.html', {'payment': payment})