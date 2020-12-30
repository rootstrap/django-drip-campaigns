from django.db import models
from django.conf import settings
from django.apps import apps as django_apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Campaign(models.Model):
    name = models.CharField(max_length=256, default='Unnamed Campaign')
    delete_drips = models.BooleanField(default=True)

    def delete(self, using=None, keep_parents=False):
        if self.delete_drips:
            self.drip_set.all().delete()
        super().delete(using, keep_parents)
