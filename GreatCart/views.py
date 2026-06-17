from django.shortcuts import render
from store.models import Product
from django.http import Http404


def home(request):
    products = Product.objects.all().order_by('-created_date')[:8]
    context = {
        'products': products,
    }
    return render(request, 'home.html', context)
