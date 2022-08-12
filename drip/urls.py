from django.conf import settings
from django.urls import re_path

from drip.views import UnsubscribeCampaignView, UnsubscribeDripView, UnsubscribeView

urlpatterns = []

if getattr(settings, "DRIP_UNSUBSCRIBE_USERS", False):
    urlpatterns += [
        re_path(
            r"^drip/(?P<drip_uidb64>\w+)/(?P<uidb64>\w+)/(?P<token>[\w-]+)/$",
            UnsubscribeDripView.as_view(),
            name="unsubscribe_drip",
        ),
        re_path(
            r"^campaign/(?P<campaign_uidb64>\w+)/(?P<uidb64>\w+)/(?P<token>[\w-]+)/$",
            UnsubscribeCampaignView.as_view(),
            name="unsubscribe_campaign",
        ),
        re_path(
            r"^app/(?P<uidb64>\w+)/(?P<token>[\w-]+)/$",
            UnsubscribeView.as_view(),
            name="unsubscribe_app",
        ),
    ]
