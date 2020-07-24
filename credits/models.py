import sys

from django.contrib.auth.models import User
from django.db import models

TESTING = ('test' in sys.argv)


class Profile(models.Model):
    """
    For testing, track the number of "credits".
    """
    user = models.OneToOneField(
        'auth.User',
        related_name='profile',
        on_delete=models.CASCADE,
    )
    credits = models.PositiveIntegerField(default=0)


def user_post_save(sender, instance, created, raw, **kwargs):
    # Use this table only when testing
    if created and TESTING:
        Profile.objects.create(user=instance)


models.signals.post_save.connect(user_post_save, sender=User)
