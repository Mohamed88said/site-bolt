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