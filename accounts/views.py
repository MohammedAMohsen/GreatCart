from django.shortcuts import render, redirect
from .form import RegisterForm
from .models import Account
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

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


def password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip().lower()
        try: 
            user = Account.objects.get(email__exact=email)
            current_site = get_current_site(request)
            mail_supject = 'Reset Your Password'
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            message = f"""
                Hi {user.first_name}
                Please click on below link to reset your password
                http://{current_site}/accounts/password-change/{uid}/{token}

                If you thick it's not you, please ingnore this email.
            """
            send_email = EmailMessage(mail_supject, message, to=[user.email])
            send_email.send()
        except Account.DoesNotExist:
            pass
        return redirect('password_reset_done')
    return render(request, 'accounts/password_reset.html')


def password_reset_done(request):
    return render(request, 'accounts/password_reset_done.html')


def password_change(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            if new_password1 == new_password2:
                user.set_password(new_password1)
                user.save()
                messages.success(request, 'Your password has been updated! You are now able to Log in')
                return redirect('login')
            else:
                messages.error(request, 'Password do not match!')            
    else:
        messages.error(request, 'That Link has been expired!')
        return redirect('login')
    return render(request, 'accounts/password_reset_confirm.html')


@login_required(login_url='login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')