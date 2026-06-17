from django.db import models
from store.models import Product, Variation

class Cart(models.Model):
    identifier = models.CharField(max_length=250, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    # Note:
    # This field acts as a cart identifier.
    # For guests it stores session_key.
    # For authenticated users it stores user.id

    def __str__(self):
        return self.identifier


class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)
    
    def sub_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return self.product.product_name