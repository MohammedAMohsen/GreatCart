from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from carts.views import _cart_id
from carts.models import CartItem
from .forms import OrderForm
from django.contrib import messages
from .models import Order, OrderProduct, Payment
import datetime
import json
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage


@login_required(login_url='login')
def place_order(request):
    cart_items = CartItem.objects.filter(cart__identifier=_cart_id(request))
    if not cart_items.exists():
        return redirect('store')
    
    pending_order = Order.objects.filter(user=request.user, is_ordered=False).first()
    if pending_order:
        messages.warning(request, 'You already have order that has not been completed!')
        return redirect('payment_page', order_number=pending_order.order_number)

    total = sum(item.quantity * item.product.price for item in cart_items)
    tax = total * 0.02
    grand_total = total + tax

    if request.method != 'POST':
        return redirect('story')
    form = OrderForm(request.POST)
    if form.is_valid():
        order = form.save(commit=False)
        order.user = request.user
        order.ip = request.META.get('REMOTE_ADDR')
        order.tax = tax
        order.order_total = grand_total
        order.save()
        order_number = f"{datetime.date.today().strftime('%Y%m%d')}{order.id}"
        order.order_number = order_number
        order.save(update_fields=['order_number'])

        # Move the cart items to Order product table
        for item in cart_items:
            order_product = OrderProduct.objects.create(
                order = order,
                user = request.user,
                product = item.product,
                quantity = item.quantity,
                product_price = item.product.price,
            )
            if item.variations.all():
                dict_variation = []
                for variation in item.variations.values():
                    dict_variation.append({'category': variation.get('variation_category'), 'value': variation.get('variation_value')})
                order_product.variations = dict_variation
                order_product.save()
        cart_items.delete()
        return redirect('payment_page', order_number=order.order_number)
    else:
        messages.error(request, 'There is an error in the order. Please try again')
        return redirect('checkout')


@login_required(login_url='login')
def payment_page(request, order_number):
    try:
        order = Order.objects.get(user=request.user, order_number=order_number)
        if order.status == 'Completed' or order.is_ordered:
            messages.info(request, 'This order has already been completed!')
            return redirect('store')
        order_product = OrderProduct.objects.filter(order=order)
        context = {
            'order': order,
            'order_product': order_product,
            'tax': round(order.tax, 2),
            'total': order.order_total - order.tax,
            'grand_total': order.order_total,
        }
    except Order.DoesNotExist:
        messages.error(request, 'Order not found!')
        return redirect('store')
    return render(request, 'orders/payments.html', context)


def payments(request):
    if request.method != 'POST':
        return JsonResponse({'message':'Invalid request'}, status=405)

    body = json.loads(request.body)
    order = Order.objects.filter(user=request.user, order_number=body['orderID']).first()

    if order.is_ordered:
        return JsonResponse({'message':'Payment already completed'}, status=400)
    
    # Check the availability of the product
    order_products = OrderProduct.objects.filter(order=order, ordered=False)
    for order_product in order_products:
        if order_product.product.stock < order_product.quantity:
            return JsonResponse({'message': f"Product '{order_product.product.product_name}' out of stock, Try agein later"}, status=400)

    # Store transaction details inside Payment model
    payment = Payment.objects.create(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status'],
    )
    order.payment = payment
    order.is_ordered = True
    order.status = 'Completed'
    order.save()

    # Completed order product and reduce the quantity of the solid products 
    for order_product in order_products:
        order_product.payment = payment
        order_product.ordered = True
        order_product.save()
        order_product.product.stock -= order_product.quantity
        order_product.product.save()
    
    # Send order recieved email to customer
    mail_supject = 'Thank you for your order!'
    message = render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order': order,
        'order_products': order_products,
        'tax': round(order.tax, 2),
        'total': order.order_total - order.tax,
        'grand_total': order.order_total,
    })
    send_email = EmailMessage(mail_supject, message, to=[request.user.email])
    send_email.send()
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)


def order_complete(request):
    order_number = request.GET.get('order_number')
    payment_id = request.GET.get('payment_id')
    try:
        order = Order.objects.get(user=request.user, order_number=order_number, payment__payment_id=payment_id)
        order_products = OrderProduct.objects.filter(order=order, ordered=True)
        context = {
            'order_products': order_products,
            'order': order,
            'subtotal': order.order_total - order.tax,
        }
    except(Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
    return render(request, 'orders/order_complete.html', context)