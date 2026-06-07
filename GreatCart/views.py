from django.shortcuts import render
from store.models import Product
from django.http import Http404


def home(request):
    products = Product.objects.all()[:8]
    context = {
        'products': products,
    }
    return render(request, 'home.html', context)
