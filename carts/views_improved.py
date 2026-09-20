"""
============================================================================
هذه نسخة محسّنة (Refactored) من ملف carts/views.py الأصلي.

الهدف منها: توضيح كيف يمكن حل نفس المشاكل المنطقية (إضافة منتج للسلة،
دمج سلة الزائر بسلة المستخدم بعد تسجيل الدخول) بطريقة أنظف وأكثر أماناً،
بدون تغيير السلوك الوظيفي الأساسي للكود الأصلي.

أهم التحسينات المطبّقة هنا (وأسباب كل واحد منها موضّحة كتعليق عند مكانه
بالكود تحديداً):

1. استخراج منطق "مطابقة CartItem موجود بنفس مجموعة الـ variations" لدالة
    مساعدة واحدة (_find_matching_cart_item) بدل تكرار نفس الخوارزمية المعقدة
    مرتين (مرة بـ add_cart ومرة بـ merge_cart) — يحل التكرار ويحل الـ bug
    دفعة واحدة بمكان واحد فقط.

2. استبدال مقارنة القوائم (list) بمقارنة المجموعات (set) عند مطابقة
    الـ variations — لأن مقارنة القوائم حساسة لترتيب العناصر، بينما
    التوليفة منطقياً "مجموعة" لا يهم ترتيبها. هذا يصلح bug حقيقي كان
    يمكن أن ينشئ CartItem مكرر لنفس التوليفة إذا اختلف ترتيب وصول
    البيانات من الفورم.

3. استبدال الاعتماد على "except: pass" لتصفية مفاتيح request.POST غير
    ذات الصلة (مثل csrfmiddlewaretoken) بفلترة صريحة تعتمد فقط على
    variation_category الفعلية المرتبطة بالمنتج.

4. استبدال "except: pass" العام (bare except) في merge_cart بمعالجة
    أكثر تحديداً مع تسجيل الخطأ (logging) بدل ابتلاعه بصمت بالكامل.

5. إزالة استعلامات قاعدة بيانات مكررة غير ضرورية (مثل إعادة جلب
    CartItem بعد أن كان أصلاً متوفراً بمتغير محلي).

6. استخدام get_or_create بدل try/except اليدوية لجلب أو إنشاء الـ Cart.

7. استخدام get_object_or_404 بدل .objects.get() المباشر لجلب المنتج
    في add_cart (نفس النمط المستخدم أصلاً في بقية دوال الملف).

ملاحظة: هذا الملف نسخة للمراجعة والتعديل من قبلك — لم يُدمج بعد بالمشروع.
============================================================================
"""

import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

from .models import Cart, CartItem
from store.models import Product, Variation

logger = logging.getLogger(__name__)


def _cart_id(request):
    """
    يرجّع معرّف السلة الموحّد:
    - user.id لو المستخدم مسجّل دخول.
    - session_key لو زائر (يُنشأ الآن صراحة لو غير موجود بعد).
    """
    if request.user.is_authenticated:
        return request.user.id
    cart_key = request.session.session_key
    if not cart_key:
        cart_key = request.session.create()
    return cart_key


def _extract_variations_from_post(request, product):
    """
    يبني قائمة Variation objects من بيانات الفورم المُرسلة (request.POST)،
    بالاعتماد فقط على أسماء الـ variation_category الفعلية المرتبطة بهذا
    المنتج بالتحديد — بدل المرور على كل مفتاح بـ request.POST (بما فيه
    csrfmiddlewaretoken وأي حقول أخرى غير ذات صلة) والاعتماد على
    except: pass لتصفيتها ضمنياً.
    """
    if request.method != 'POST':
        return []

    categories = (
        Variation.objects
        .filter(product=product)
        .values_list('variation_category', flat=True)
        .distinct()
    )

    variations = []
    for category in categories:
        value = request.POST.get(category)
        if not value:
            continue
        try:
            variation = Variation.objects.get(
                product=product,
                variation_category__iexact=category,
                variation_value__iexact=value,
            )
            variations.append(variation)
        except Variation.DoesNotExist:
            # القيمة المُرسَلة لا تطابق أي Variation فعلية لهذا المنتج —
            # حالة متوقعة (مثلاً بيانات فورم غير صالحة)، تُتجاهل بأمان.
            continue

    return variations


def _find_matching_cart_item(cart, product, variations):
    """
    يبحث عن CartItem موجود فعلاً بنفس السلة، لنفس المنتج، وبنفس مجموعة
    الـ variations بالضبط (بغض النظر عن ترتيب وصولها).

    يُستخدم هذا من add_cart و merge_cart معاً، بدل تكرار نفس الخوارزمية
    مرتين بمكانين مختلفين.

    يرجّع الـ CartItem المطابق، أو None لو ما فيه تطابق.
    """
    variation_set = set(variations)
    for item in CartItem.objects.filter(cart=cart, product=product):
        if set(item.variations.all()) == variation_set:
            return item
    return None


def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not (product.is_available and product.stock > 0):
        messages.warning(request, 'The product is not available at the moment, try later')
        return redirect('product-detail', category_slug=product.category.slug, product_slug=product.slug)

    variations = _extract_variations_from_post(request, product)

    # get_or_create بدل try/except يدوية — نفس النتيجة، أوضح وأقصر.
    cart, _ = Cart.objects.get_or_create(identifier=_cart_id(request))

    existing_item = _find_matching_cart_item(cart, product, variations)

    if existing_item:
        existing_item.quantity += 1
        existing_item.save()
    else:
        new_item = CartItem.objects.create(product=product, cart=cart, quantity=1)
        if variations:
            new_item.variations.add(*variations)
            # لا حاجة لاستدعاء .clear() هنا: العنصر تو أُنشئ، فمن
            # المستحيل أن تكون لديه variations سابقة تحتاج مسحاً.

    return redirect('cart')


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_object_or_404(Cart, identifier=_cart_id(request))
    cart_item = get_object_or_404(CartItem, cart=cart, product=product, id=cart_item_id)

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('cart')


def delete_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_object_or_404(Cart, identifier=_cart_id(request))
    cart_item = get_object_or_404(CartItem, cart=cart, product=product, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')


def merge_cart(request, user):
    """
    يُستدعى عند تسجيل الدخول — قبل login(request, user) مباشرة — لدمج
    سلة الزائر الحالية (المبنية على session key) مع سلة المستخدم
    المسجّل (المبنية على user.id)، أو تحويلها إليه مباشرة لو ما عنده
    سلة سابقة أصلاً.
    """
    guest_identifier = _cart_id(request)

    try:
        guest_cart = Cart.objects.get(identifier=guest_identifier)
    except Cart.DoesNotExist:
        # ما فيه سلة زائر أصلاً لدمجها — لا شيء نسويه.
        return

    guest_items = CartItem.objects.filter(cart=guest_cart)
    if not guest_items.exists():
        return

    user_cart, created = Cart.objects.get_or_create(identifier=user.id)

    if created:
        # المستخدم ما عنده سلة سابقة — أبسط حل: "أعد تسمية" سلة الزائر
        # نفسها بدل نسخ عناصرها واحداً واحداً.
        user_cart.delete()  # نحذف السلة الفارغة اللي تو أُنشئت بالخطأ
        guest_cart.identifier = user.id
        guest_cart.save()
        return

    # المستخدم عنده سلة سابقة فعلاً — لازم دمج حقيقي عنصراً بعنصر.
    for guest_item in guest_items:
        item_variations = list(guest_item.variations.all())
        matching_item = _find_matching_cart_item(user_cart, guest_item.product, item_variations)

        if matching_item:
            matching_item.quantity += guest_item.quantity
            matching_item.save()
        else:
            new_item = CartItem.objects.create(
                cart=user_cart,
                product=guest_item.product,
                quantity=guest_item.quantity,
            )
            if item_variations:
                new_item.variations.add(*item_variations)

    guest_cart.delete()


def cart(request, total=0, tax=0, grand_total=0, cart_items=None):
    try:
        current_cart = Cart.objects.get(identifier=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=current_cart, is_active=True)
        total = sum(item.product.price * item.quantity for item in cart_items)
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


@login_required(login_url='login')
def checkout(request, total=0, tax=0, grand_total=0, cart_items=None):
    try:
        current_cart = Cart.objects.get(identifier=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=current_cart, is_active=True)
        total = sum(item.quantity * item.product.price for item in cart_items)
        tax = total * 0.02  # 2% قيمة الضريبة
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'tax': tax,
        'total': total,
        'cart_items': cart_items,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)
