from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import SalesAnalytics, ProductView
from orders.models import Order
from products.models import Product

@login_required
def dashboard(request):
    """Analytics dashboard for sellers."""
    if not request.user.is_seller:
        return redirect('core:home')
    
    # Date range (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Sales analytics
    sales_data = SalesAnalytics.objects.filter(
        seller=request.user,
        date__range=[start_date, end_date]
    ).aggregate(
        total_sales=Sum('total_sales'),
        total_orders=Sum('total_orders'),
        avg_order_value=Avg('average_order_value')
    )
    
    # Product performance
    products = Product.objects.filter(seller=request.user)
    product_stats = {
        'total_products': products.count(),
        'active_products': products.filter(is_active=True).count(),
        'out_of_stock': products.filter(stock=0).count(),
        'low_stock': products.filter(stock__lte=5, stock__gt=0).count(),
    }
    
    # Recent orders
    recent_orders = Order.objects.filter(
        items__product__seller=request.user
    ).distinct().order_by('-created_at')[:10]
    
    # Top products
    top_products = products.annotate(
        total_sold=Count('orderitem')
    ).order_by('-total_sold')[:5]
    
    context = {
        'sales_data': sales_data,
        'product_stats': product_stats,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'date_range': f"{start_date} - {end_date}",
    }
    
    return render(request, 'analytics/dashboard.html', context)