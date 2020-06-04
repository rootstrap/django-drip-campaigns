#from django.contrib.auth.models import User
from django.db import models
#from drip.utils import get_user_model #prueba
from django.contrib.auth import get_user_model

USER = get_user_model() #prueba

class Profile(models.Model):
    """
    For testing, track the number of "credits".
    """
    user = models.OneToOneField(
        USER,
        related_name='profile',
        on_delete=models.CASCADE,
    )
    credits = models.PositiveIntegerField(default=0)


def user_post_save(sender, instance, created, raw, **kwargs):
    if created:
        Profile.objects.create(user=instance)
models.signals.post_save.connect(user_post_save, sender=USER)
