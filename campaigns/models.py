from django.db import models
from django.conf import settings
from django.apps import apps as django_apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Campaign(models.Model):
    name = models.CharField(max_length=256, default='Unnamed Campaign')
    delete_drips = models.BooleanField(default=True)

    @property
    def drips(self):
        Drip = django_apps.get_model(settings.DRIP_CLASS_NAME)
        return Drip.objects.filter(
            id__in=self.campaign_drips.values_list('id', flat=True)
        )

    def delete(self, using=None, keep_parents=False):
        if self.delete_drips:
            self.drips.delete()
        super().delete(using, keep_parents)


class CampaignDrip(models.Model):
    # This implementation is based on:
    #  https://docs.djangoproject.com/en/3.0/ref/contrib/contenttypes/
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    drip_id = models.PositiveIntegerField()
    drip = GenericForeignKey('content_type', 'drip_id')
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='campaign_drips'
    )
