from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Payment, PaymentConfirmation, PaymentDispute
from deliveries.models import Delivery
from notifications.models import Notification
from django.db.models import F
from django.http import JsonResponse
from .stripe_utils import StripePaymentProcessor
from .mobile_money import MobileMoneyProcessor
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@csrf_exempt
def qr_scan_payment(request, payment_id):
    """Vue appelée quand le QR code est scanné par l'acheteur"""
    payment = get_object_or_404(Payment, id=payment_id)
    order = payment.order
    delivery = getattr(order, 'delivery', None)
    
    if payment.status not in ['pending', 'awaiting_scan']:
        return render(request, 'payments/qr_scan_error.html', {
            'error': 'Ce paiement a déjà été traité ou est expiré.',
            'payment': payment
        })
    
    # Marquer comme scanné
    payment.status = 'scanned_pending_payment'
    payment.save()
    
    # Déterminer qui paie la livraison
    delivery_paid_by_buyer = True
    if delivery:
        delivery_paid_by_buyer = delivery.paid_by == 'buyer'
        # Vérifier si le vendeur prend en charge la livraison pour ses produits
        for item in order.items.all():
            if item.product.seller_pays_delivery:
                delivery_paid_by_buyer = False
                delivery.paid_by = 'seller'
                delivery.save()
                break
    
    context = {
        'payment': payment,
        'order': order,
        'delivery': delivery,
        'delivery_paid_by_buyer': delivery_paid_by_buyer,
        'total_amount': payment.amount,
        'delivery_cost': delivery.delivery_cost if delivery else 0,
        'product_total': order.total_amount,
        'is_guinea': True,  # Spécifique à la Guinée
        'available_methods': [
            {'key': 'stripe', 'name': 'Carte bancaire', 'icon': 'fas fa-credit-card'},
            {'key': 'paypal', 'name': 'PayPal', 'icon': 'fab fa-paypal'},
            {'key': 'mobile_money', 'name': 'Mobile Money', 'icon': 'fas fa-mobile-alt'},
            {'key': 'cash', 'name': 'Espèces', 'icon': 'fas fa-money-bill-wave'},
        ]
    }
    
    return render(request, 'payments/qr_scan_payment.html', context)

@login_required
def process_qr_payment(request, payment_id):
    """Traiter le paiement après scan du QR code"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.status != 'scanned_pending_payment':
        return JsonResponse({'success': False, 'error': 'Paiement non valide'})
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        confirmation_code = request.POST.get('confirmation_code')
        
        # Vérifier le code de confirmation
        if confirmation_code != payment.confirmation_code:
            payment.confirmation_attempts += 1
            payment.save()
            return JsonResponse({
                'success': False, 
                'error': f'Code incorrect. Tentatives restantes: {3 - payment.confirmation_attempts}'
            })
        
        if payment_method == 'cash':
            # Paiement en espèces - confirmer immédiatement
            payment.status = 'completed'
            payment.payment_method = 'cash_on_delivery'
            payment.confirmed_at = timezone.now()
            payment.save()
            
            # Mettre à jour la commande
            payment.order.payment_status = 'completed'
            payment.order.status = 'delivered'
            payment.order.save()
            
            return JsonResponse({
                'success': True, 
                'message': 'Paiement en espèces confirmé',
                'redirect_url': reverse('orders:detail', kwargs={'pk': payment.order.id})
            })
        
        elif payment_method in ['stripe', 'paypal', 'mobile_money']:
            # Rediriger vers le processeur de paiement approprié
            payment.payment_method = payment_method
            payment.status = 'processing'
            payment.save()
            
            if payment_method == 'stripe':
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('payments:create_stripe_payment', kwargs={'order_id': payment.order.id})
                })
            elif payment_method == 'paypal':
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('payments:create_paypal_payment', kwargs={'order_id': payment.order.id})
                })
            elif payment_method == 'mobile_money':
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('payments:create_mobile_money_payment', kwargs={'order_id': payment.order.id})
                })
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@login_required
def create_stripe_payment(request, order_id):
    """Créer un paiement Stripe"""
    from orders.models import Order
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        try:
            # Créer ou récupérer le paiement
            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'payment_method': 'stripe',
                    'amount': order.total_with_shipping,
                    'status': 'pending'
                }
            )
            
            # Créer le PaymentIntent Stripe
            intent = StripePaymentProcessor.create_payment_intent(
                amount=payment.amount,
                metadata={
                    'order_id': str(order.id),
                    'payment_id': str(payment.id)
                }
            )
            
            if intent:
                payment.stripe_payment_intent_id = intent.id
                payment.save_gateway_response(intent)
                payment.save()
                
                return JsonResponse({
                    'success': True,
                    'client_secret': intent.client_secret,
                    'payment_id': str(payment.id)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Erreur lors de la création du paiement'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@login_required
def create_mobile_money_payment(request, order_id):
    """Créer un paiement Mobile Money"""
    from orders.models import Order
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            provider = data.get('provider', 'orange')
            
            if not phone_number:
                return JsonResponse({
                    'success': False,
                    'error': 'Numéro de téléphone requis'
                })
            
            # Créer ou récupérer le paiement
            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'payment_method': 'mobile_money',
                    'amount': order.total_with_shipping,
                    'status': 'pending',
                    'mobile_money_phone': phone_number,
                    'mobile_money_provider': provider
                }
            )
            
            # Initier le paiement Mobile Money
            processor = MobileMoneyProcessor()
            result = processor.initiate_payment(
                amount=payment.amount,
                phone_number=phone_number,
                provider=provider,
                reference=f"ORDER_{order.id}"
            )
            
            if result and result.get('success'):
                payment.mobile_money_transaction_id = result.get('transaction_id')
                payment.status = 'processing'
                payment.save_gateway_response(result)
                payment.save()
                
                return JsonResponse({
                    'success': True,
                    'transaction_id': result.get('transaction_id'),
                    'message': 'Paiement initié. Vérifiez votre téléphone.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Erreur lors de l\'initiation du paiement'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@login_required
def payment_success(request, payment_id):
    """Page de succès après paiement"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Vérifier que l'utilisateur a le droit de voir ce paiement
    if payment.order.user != request.user:
        messages.error(request, "Vous n'avez pas accès à ce paiement.")
        return redirect('orders:list')
    
    return render(request, 'payments/success.html', {
        'payment': payment,
        'order': payment.order
    })

def mobile_money_callback(request):
    """Callback pour les notifications Mobile Money"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            transaction_id = data.get('transaction_id')
            status = data.get('status')
            
            if transaction_id:
                payment = Payment.objects.filter(
                    mobile_money_transaction_id=transaction_id
                ).first()
                
                if payment:
                    if status == 'success':
                        payment.status = 'completed'
                        payment.confirmed_at = timezone.now()
                        payment.order.payment_status = 'completed'
                        payment.order.save()
                    elif status == 'failed':
                        payment.status = 'failed'
                    
                    payment.save_gateway_response(data)
                    payment.save()
                    
                    return JsonResponse({'success': True})
            
            return JsonResponse({'success': False, 'error': 'Transaction non trouvée'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@login_required
def confirm_payment(request, payment_id):
    """Vue pour confirmer le paiement après scan du QR code ou saisie manuelle"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.status != 'pending':
        messages.error(request, _("Ce paiement a déjà été traité ou annulé."))
        return redirect('orders:detail', pk=payment.order.id)
    
    delivery = getattr(payment.order, 'delivery', None)
    if not delivery:
        messages.error(request, _("Aucune livraison associée à ce paiement."))
        return redirect('orders:detail', pk=payment.order.id)
    
    # Vérifier que l'utilisateur est autorisé (acheteur ou vendeur selon paid_by)
    is_seller = payment.order.items.first().product.seller == request.user
    is_buyer = payment.order.user == request.user
    if not (is_buyer and delivery.paid_by == 'buyer') and not (is_seller and delivery.paid_by == 'seller'):
        messages.error(request, _("Vous n'êtes pas autorisé à confirmer ce paiement."))
        return redirect('orders:detail', pk=payment.order.id)
    
    # Vérifier le nombre de tentatives et l'expiration du QR code
    if payment.confirmation_attempts >= 3:
        messages.error(request, _("Trop de tentatives. Veuillez signaler un litige."))
        return render(request, 'payments/confirmation_page.html', {
            'payment': payment,
            'order': payment.order,
            'order_items': payment.order.items.all(),
            'delivery': delivery,
            'error': 'Trop de tentatives. Veuillez signaler un litige.'
        })
    
    if payment.qr_code_expires_at and payment.qr_code_expires_at < timezone.now():
        messages.error(request, _("Le QR code a expiré."))
        return render(request, 'payments/confirmation_page.html', {
            'payment': payment,
            'order': payment.order,
            'order_items': payment.order.items.all(),
            'delivery': delivery,
            'error': 'Le QR code a expiré.'
        })
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        confirmation_code = request.POST.get('confirmation_code')
        paid_by = request.POST.get('paid_by', delivery.paid_by)
        
        # Vérifier le code de confirmation
        if confirmation_code != payment.confirmation_code:
            payment.confirmation_attempts += 1
            payment.save()
            messages.error(request, _("Code de confirmation incorrect."))
            return render(request, 'payments/confirmation_page.html', {
                'payment': payment,
                'order': payment.order,
                'order_items': payment.order.items.all(),
                'delivery': delivery,
                'error': f"Code incorrect. Tentatives restantes : {3 - payment.confirmation_attempts}"
            })
        
        # Mettre à jour paid_by si modifié par le vendeur
        if is_seller and paid_by in ['buyer', 'seller'] and paid_by != delivery.paid_by:
            delivery.paid_by = paid_by
            delivery.save()
        
        # Simuler le paiement par carte avec Stripe
        if payment_method == 'card':
            payment.status = 'processing'
            payment.save()
            messages.success(request, _("Paiement par carte en cours de traitement."))
            return redirect('orders:detail', pk=payment.order.id)
        
        # Paiement en espèces
        elif payment_method == 'cash':
            payment.status = 'pending_delivery_confirmation'
            payment.save()
            
            PaymentConfirmation.objects.create(
                payment=payment,
                confirmed_by=request.user,
                confirmation_method='qr_code' if confirmation_code else 'manual_code',
                notes=f"Paiement en espèces initié par {delivery.get_paid_by_display()} pour la commande {payment.order.id}"
            )
            
            if delivery and delivery.delivery_person:
                Notification.objects.create(
                    user=delivery.delivery_person,
                    title=_('Confirmation de paiement requise'),
                    message=f"Veuillez confirmer la réception du paiement en espèces pour la livraison #{delivery.tracking_number} par {delivery.get_paid_by_display()}.",
                    notification_type='payment_confirmation',
                    url=reverse('payments:confirm_cash_payment', kwargs={'payment_id': payment.id})
                )
            
            messages.success(request, _("Paiement en espèces initié. En attente de confirmation par le livreur."))
            return redirect('orders:detail', pk=payment.order.id)
        
    return render(request, 'payments/confirmation_page.html', {
        'payment': payment,
        'order': payment.order,
        'order_items': payment.order.items.all(),
        'delivery': delivery
    })

@login_required
def confirm_cash_payment(request, payment_id):
    """Vue pour permettre au livreur de confirmer la réception du paiement en espèces"""
    payment = get_object_or_404(Payment, id=payment_id, status='pending_delivery_confirmation')
    delivery = get_object_or_404(Delivery, order=payment.order, delivery_person=request.user)
    
    if request.method == 'POST':
        payment.status = 'completed'
        payment.confirmed_at = timezone.now()
        payment.save()
        
        PaymentConfirmation.objects.filter(payment=payment).update(
            notes=F('notes') + f"\nConfirmation finale par le livreur le {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        payment.order.payment_status = 'completed'
        payment.order.status = 'delivered'
        payment.order.save()
        
        messages.success(request, _("Paiement en espèces confirmé avec succès."))
        return redirect('deliveries:detail', pk=delivery.id)
    
    return render(request, 'payments/confirm_cash_payment.html', {
        'payment': payment,
        'order': payment.order,
        'delivery': delivery
    })

@login_required
def dispute_payment(request, payment_id):
    """Vue pour signaler un litige sur un paiement"""
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        evidence = request.FILES.get('evidence')
        dispute = PaymentDispute.objects.create(
            payment=payment,
            user=request.user,
            reason=reason,
            evidence=evidence
        )
        Notification.objects.create(
            user=payment.order.user,
            title="Nouveau litige signalé",
            message=f"Un litige a été signalé pour le paiement {payment.id}.",
            notification_type='system',
            url=reverse('payments:dispute_detail', args=[dispute.id])
        )
        messages.success(request, _("Litige signalé avec succès."))
        return redirect('payments:dispute_detail', dispute_id=dispute.id)
    return render(request, 'payments/dispute_form.html', {'payment': payment})

@login_required
def dispute_detail(request, dispute_id):
    """Vue pour afficher les détails d'un litige"""
    dispute = get_object_or_404(PaymentDispute, id=dispute_id, user=request.user)
    return render(request, 'payments/dispute_detail.html', {'dispute': dispute})