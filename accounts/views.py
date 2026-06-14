from django.shortcuts import render, redirect
from .form import RegisterForm
from .models import Account
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import reverse_lazy

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
    return render(request, 'accounts/dashboard.html')