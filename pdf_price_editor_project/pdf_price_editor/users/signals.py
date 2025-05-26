from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create or update UserProfile when a User instance is saved.
    """
    if created:
        UserProfile.objects.create(user=instance)
    # Ensure profile is saved whenever the user is saved.
    # This handles updates to the user that might affect the profile,
    # or if the profile was somehow not created initially.
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        # This case should ideally be handled by the created block,
        # but as a fallback, create it if it doesn't exist.
        UserProfile.objects.create(user=instance)
