from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class MyAccountManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, password=None):
        if not email:
            raise ValueError('User must have an email address')
        if not username:
            raise ValueError('User must have an username')
        
        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, first_name, last_name, username, email, password): 
        user = self.create_user(
            email = self.normalize_email(email),
            username = username,
            password = password,
            first_name = first_name,
            last_name = last_name)
        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user


class Account(AbstractBaseUser):
    first_name    = models.CharField(max_length=50)
    last_name     = models.CharField(max_length=50)
    phone_number  = models.CharField(max_length=50)
    username      = models.CharField(max_length=50, unique=True)
    email         = models.EmailField(max_length=100, unique=True)
    # required
    date_joined    = models.DateTimeField(auto_now_add=True)
    last_login     = models.DateTimeField(auto_now=True)
    is_admin       = models.BooleanField(default=False)
    is_staff       = models.BooleanField(default=False)
    is_active      = models.BooleanField(default=False)
    is_superadmin  = models.BooleanField(default=False)
    
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = MyAccountManager()

    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, add_label):
        return True


# ------------------------------------------------------------------
# Note:
#
# This project uses the classic AbstractBaseUser approach and manually
# implements has_perm() and has_module_perms().
#
# In modern Django projects, it is common to inherit from:
#
#     PermissionsMixin
#
# Example:
#
#     class Account(AbstractBaseUser, PermissionsMixin):
#
# Benefits of PermissionsMixin:
#
# - Provides has_perm() automatically.
# - Provides has_module_perms() automatically.
# - Adds the is_superuser & is_admin field automatically.
# - Supports Django's built-in permissions system.
# - Supports Groups and User Permissions.
# - Better integration with Django Admin.
# - Reduces custom authentication code.
#
# This project follows the instructor's implementation for learning
# purposes and compatibility with the course code.
# ------------------------------------------------------------------