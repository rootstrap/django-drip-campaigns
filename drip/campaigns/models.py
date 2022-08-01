from django.db import models


class Campaign(models.Model):
    name = models.CharField(max_length=256)
    delete_drips = models.BooleanField(default=True)

    def delete(self, using=None, keep_parents=False):
        if self.delete_drips:
            self.drip_set.all().delete()
        super().delete(using, keep_parents)

    def __str__(self) -> str:
        return self.name
