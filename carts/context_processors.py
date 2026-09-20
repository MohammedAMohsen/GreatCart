from .models import Cart, CartItem
from .views import _cart_id
from django.db.models import Sum

def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.get(identifier = _cart_id(request))
            cart_count = CartItem.objects.filter(cart=cart).aggregate(total=Sum('quantity'))['total'] or 0 
        except Cart.DoesNotExist:
            cart_count = 0    
    return dict(cart_count=cart_count)