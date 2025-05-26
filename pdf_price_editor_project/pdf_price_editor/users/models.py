from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    USER_LANGUAGE_CHOICES = [
        ('uk', 'Ukrainian'),
        ('it', 'Italian'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    preferred_language = models.CharField(
        max_length=10,
        choices=USER_LANGUAGE_CHOICES,
        default='uk'
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"
