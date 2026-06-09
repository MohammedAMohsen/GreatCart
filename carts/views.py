from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem
from store.models import Product, Variation
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id) # get the product
    product_variation = []

    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST.get(key)
            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)
            except:
                pass

    if product.is_available and product.stock > 0:

        try:
            cart = Cart.objects.get(cart_id=_cart_id(request)) # get the cart useing the cart_id present in the session
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()
        
        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            all_variations = []
            id = []
            for item in cart_item:
                all_variations.append(list(item.variations.all()))
                id.append(item.id)
            if product_variation in all_variations:
                index = all_variations.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(id=item_id ,product=product)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(product=product, cart=cart,  quantity=1)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(product=product, cart=cart, quantity=1)
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('cart')
    
    else:
        messages.warning(request, 'The product is not available at the moment, try later')
        return redirect('product-detail', category_slug=product.category.slug ,product_slug=product.slug)


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart.objects.get(cart_id=_cart_id(request))
    cart_item = get_object_or_404(CartItem, cart=cart, product=product, id=cart_item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()  
    else:
        cart_item.delete()
    return redirect('cart')


def delete_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart.objects.get(cart_id=_cart_id(request))
    cart_item = get_object_or_404(CartItem, cart=cart, product=product, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')


def cart(request, total=0, tax=0, grand_total=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
        tax = (2 * total) / 100  # 2% قيمة الضريبة 
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'tax': tax,
        'total': total,
        'cart_items': cart_items,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)