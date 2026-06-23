from django.contrib import admin
from .models import Order, Payment, OrderProduct

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0
    readonly_fields = ('product', 'variations', 'quantity', 'product_price', 'order', 'payment', 'user', 'ordered')
    
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'full_name', 'phone', 'email', 'city', 'order_total', 'tax', 'status', 'is_ordered', 'cerated_at')
    search_fields = ('order_number', 'first_name', 'last_name', 'phone', 'email')
    list_filter = ('status', 'is_ordered')
    list_per_page = 20
    inlines = [OrderProductInline]

class OrderProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'variations', 'quantity', 'product_price', 'order', 'payment', 'user', 'ordered')


admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(OrderProduct,OrderProductAdmin)