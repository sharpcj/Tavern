"""Signal handlers for the profiles app."""

from __future__ import annotations

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_for_user(sender, instance, created, **kwargs):
    """Auto-create an empty Profile when a User is created."""
    if created:
        Profile.objects.create(user=instance)
