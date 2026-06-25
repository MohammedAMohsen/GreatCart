from django.shortcuts import render, get_object_or_404, redirect
from store.models import Product, Variation, ReviewRating
from category.models import category
from django.db.models import Q
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import Paginator
from orders.models import OrderProduct


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


def product_detail(request, category_slug, product_slug, is_ordered=''):
    url = request.META.get('HTTP_REFERER')
    single_product = get_object_or_404(Product, slug=product_slug, category__slug=category_slug)
    in_cart = CartItem.objects.filter(cart__identifier=_cart_id(request), product=single_product).exists()
    is_has_variation = Variation.objects.filter(product=single_product).exists()
    if request.user.is_authenticated:
        user_has_review = ReviewRating.objects.filter(user=request.user, product=single_product).exists()
        is_ordered = OrderProduct.objects.filter(product=single_product, user=request.user, ordered=True).exists()
    review_rating = ReviewRating.objects.filter(product=single_product, status=True).order_by('-created_at')
    if request.method == 'POST':
        if not user_has_review:
            ReviewRating.objects.create(
                user = request.user,
                product = single_product,
                review = request.POST.get('review'),
                rating=request.POST.get('rating', 0.0),
                ip = request.META.get('REMOTE_ADDR')
            )
        else:
            review_user = ReviewRating.objects.get(user=request.user, product=single_product)
            review_user.review = request.POST.get('review')
            review_user.rating = request.POST.get('rating', 0.0)
            review_user.save()
        return redirect(url)

    context = {
        'single_product': single_product,
        'is_has_variation': is_has_variation,
        'in_cart': in_cart,
        'review_rating': review_rating,
        'is_ordered': is_ordered,
        'url': url
    }
    return render(request, 'store/product_detail.html', context)