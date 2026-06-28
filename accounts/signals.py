"""
This file automatically creates a Profile whenever a new Account is created.

Why use signals?
- Keeps the profile creation logic in one place.
- Works no matter where the Account is created
(register view, admin panel, shell, management command, API, etc.).

For very small projects, creating the Profile directly inside the
register() view is also perfectly acceptable and often easier to follow.
"""

from django.db.models.signals import post_save
from .models import Account, Profile
from django.dispatch import receiver


@receiver(post_save, sender=Account)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# Save the related Profile whenever the Account is saved.
# Mostly useful in larger projects where the user can be updated from multiple places.
# ----------------
# @receiver(post_save, sender=Account)
# def save_profile(sender, instance, **kwargs):
#     instance.profile.save()
# ----------------
# >> يعني بالمشورع الحالي ما الها داعي ما بستخدمها 