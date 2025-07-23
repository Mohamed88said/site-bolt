from django import template
from products.models import Product

register = template.Library()

@register.filter
def is_available_in_zone(product, user_location):
    if not isinstance(product, Product) or not user_location:
        return False
    return product.is_available_in_zone(user_location)