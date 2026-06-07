from django.shortcuts import render, get_object_or_404
from store.models import Product
from django.contrib import messages
from category.models import category
from django.db.models import Q
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import Paginator


def product_paginator(request, products):
    page = request.GET.get('page')
    paginator = Paginator(products, 6)
    return paginator.get_page(page)


def store(request, category_slug=None):
    if category_slug:
        categories = get_object_or_404(category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
    else:
        products = Product.objects.filter(is_available=True)
    count = products.count()

    products = product_paginator(request, products)
    context = {
        'products': products,
        'count': count,
    }
    return render(request, 'store/store.html', context)


def search(request):
    q = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(product_name__icontains=q)|
        Q(description__icontains=q)|
        Q(category__category_name__icontains=q)|
        Q(category__slug__icontains=q),
        is_available=True
    ).order_by('-created_date')
    count = products.count()
    products = product_paginator(request, products)
    context = {
        'products': products,
        'count': count,
    }
    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    single_product = get_object_or_404(Product, slug=product_slug, category__slug=category_slug)
    in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    context = {
        'single_product': single_product,
        'in_cart': in_cart
    }
    return render(request, 'store/product_detail.html', context)