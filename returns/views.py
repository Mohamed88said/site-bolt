from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from .models import ReturnRequest, ReturnItem
from .forms import ReturnRequestForm, ReturnItemForm
from orders.models import Order

class ReturnRequestListView(LoginRequiredMixin, ListView):
    model = ReturnRequest
    template_name = 'returns/list.html'
    context_object_name = 'return_requests'
    paginate_by = 10
    
    def get_queryset(self):
        return ReturnRequest.objects.filter(user=self.request.user)

class ReturnRequestDetailView(LoginRequiredMixin, DetailView):
    model = ReturnRequest
    template_name = 'returns/detail.html'
    context_object_name = 'return_request'
    
    def get_queryset(self):
        return ReturnRequest.objects.filter(user=self.request.user)

@login_required
def create_return_request(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Vérifier si la commande peut être retournée
    if order.status not in ['delivered']:
        messages.error(request, 'Cette commande ne peut pas être retournée.')
        return redirect('orders:detail', pk=order.pk)
    
    # Vérifier si une demande de retour existe déjà
    if order.return_requests.exists():
        messages.error(request, 'Une demande de retour existe déjà pour cette commande.')
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        form = ReturnRequestForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                return_request = form.save(commit=False)
                return_request.order = order
                return_request.user = request.user
                return_request.save()
                
                # Créer les articles de retour pour tous les articles de la commande
                for order_item in order.items.all():
                    ReturnItem.objects.create(
                        return_request=return_request,
                        order_item=order_item,
                        quantity=order_item.quantity,
                        condition='À évaluer'
                    )
                
                messages.success(request, 'Votre demande de retour a été créée avec succès!')
                return redirect('returns:detail', pk=return_request.pk)
    else:
        form = ReturnRequestForm()
    
    return render(request, 'returns/create.html', {
        'form': form,
        'order': order
    })

@login_required
def cancel_return_request(request, pk):
    return_request = get_object_or_404(ReturnRequest, pk=pk, user=request.user)
    
    if return_request.can_be_cancelled:
        return_request.status = 'cancelled'
        return_request.save()
        messages.success(request, 'Votre demande de retour a été annulée.')
    else:
        messages.error(request, 'Cette demande de retour ne peut pas être annulée.')
    
    return redirect('returns:detail', pk=pk)