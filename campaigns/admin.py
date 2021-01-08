from django.contrib import admin
from campaigns.models import Campaign
from drip.models import Drip


class DripInline(admin.TabularInline):
    model = Drip


class CampaignAdmin(admin.ModelAdmin):
    inlines = [
        DripInline,
    ]


admin.site.register(Campaign, CampaignAdmin)
