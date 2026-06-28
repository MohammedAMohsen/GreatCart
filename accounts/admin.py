from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, Profile
from django.utils.html import format_html


class AccountAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'last_login', 'date_joined', 'is_active')
    list_display_links = ('email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    ordering = ('date_joined',)
    
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'state', 'country')
    
admin.site.register(Account, AccountAdmin)
admin.site.register(Profile, ProfileAdmin)
