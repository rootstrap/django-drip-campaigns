from django.conf import settings
from django.db import models


class Campaign(models.Model):
    name = models.CharField(max_length=256)
    delete_drips = models.BooleanField(default=True)
    unsubscribed_users = models.ManyToManyField(
        getattr(settings, "AUTH_USER_MODEL", "auth.User"),
        through="UserUnsubscribeCampaign",
        related_name="campaign_unsubscribed_users",
    )

    def delete(self, using=None, keep_parents=False):
        if self.delete_drips:
            self.drip_set.all().delete()
        super().delete(using, keep_parents)

    def __str__(self) -> str:
        return self.name


class UserUnsubscribeCampaign(models.Model):
    campaign = models.ForeignKey(
        Campaign,
        related_name="user_unsubscribe_campaigns",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        getattr(settings, "AUTH_USER_MODEL", "auth.User"),
        related_name="user_unsubscribe_campaigns",
        on_delete=models.CASCADE,
    )
    created_date = models.DateTimeField(auto_now_add=True)
