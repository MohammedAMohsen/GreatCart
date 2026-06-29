from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import reverse_lazy
from carts.views import merge_cart
from orders.models import Order, OrderProduct, StatusProduct
from .form import RegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import Account

# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Create Profile User (Manual) or (automatically)
            # ---------------------------------------------------------------
            # Option 1 (Simple Projects):
            # Create the Profile directly here.
            # Uncomment the line below if you are NOT using Django signals.
            # Profile.objects.create(user=user)

            # Option 2 (Recommended for Larger Projects): (Use Now ...)
            # The Profile is created automatically by the post_save signal
            # defined in accounts/signals.py, so no extra code is needed here.
            # ---------------------------------------------------------------

            # User Activetion
            current_site = get_current_site(request)
            mail_supject = 'please actiave your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_email = EmailMessage(mail_supject, message, to=[user.email])
            send_email.send()
            return redirect('/accounts/login/?command=verification&email='+user.email)
        else:
            messages.error(request, 'An error occured during registration')
    context = { 'form': form }
    return render(request, 'accounts/register.html', context)


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user= None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulation! Your account is activated. You are now able to login')
        return redirect('login')
    else:
        messages.error(request, 'Invalid acivation link')
        return redirect('register')


def login_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        email = request.POST.get('email').strip().lower()
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            merge_cart(request, user)
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, 'Invalid email or password !')
    return render(request, 'accounts/login.html')


def logout_page(request):
    logout(request)
    return redirect('login')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    success_url = reverse_lazy('login')
    def form_valid(self, form):
        messages.success(self.request, 'Your password has been updated successfully. You can now login.')
        return super().form_valid(form)


@login_required(login_url='login')
def dashboard(request):
    order = Order.objects.filter(user=request.user, status='Completed').order_by('-cerated_at').first()
    recent_orders = OrderProduct.objects.filter(order=order)[:4]
    context = {'recent_orders': recent_orders}
    return render(request, 'accounts/dashboard.html', context)


@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-cerated_at')
    context = {'orders': orders}
    return render(request, 'accounts/my_orders.html', context)


@login_required(login_url='login')
def profile_setting(request):
    if request.method == "POST":
        UserForm = UserUpdateForm(request.POST, instance=request.user)
        ProfileForm = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if UserForm.is_valid() and ProfileForm.is_valid():
            UserForm.save()
            ProfileForm.save()
            messages.success(request, 'Your account has been updated!')
        else:
            messages.error(request, 'There is something error')
    else:
        UserForm = UserUpdateForm(instance=request.user)
        ProfileForm = ProfileUpdateForm(instance=request.user.profile)
    context = {
        'UserForm': UserForm,
        'ProfileForm': ProfileForm
    }
    return render(request, 'accounts/profile_setting.html', context)