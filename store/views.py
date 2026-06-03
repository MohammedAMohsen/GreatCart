from django.shortcuts import render, get_object_or_404, redirect
from store.models import Product
from django.contrib import messages
from category.models import category
from django.db.models import Q


def store(request, category_slug=None):
    if category_slug:
        categories = get_object_or_404(category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
    else:
        q = request.GET.get('q', '')
        products = Product.objects.filter(
            Q (product_name__icontains=q) |
            Q (description__icontains=q) |
            Q (category__category_name__icontains=q) |
            Q (category__slug__icontains=q),
            is_available=True
        )
    context = {
        'products': products,
    }
    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    single_product = get_object_or_404(Product, slug=product_slug, category__slug=category_slug)
    context = {
        'single_product': single_product,
    }
    return render(request, 'store/product_detail.html', context)