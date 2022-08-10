from django.conf import settings
from django.urls import re_path

from drip.views import UnsubscribeDripView

urlpatterns = []

if getattr(settings, "DRIP_UNSUBSCRIBE_USERS", False):
    urlpatterns += [
        re_path(
            r"^drip/(?P<drip_uidb64>\w+)/(?P<uidb64>\w+)/(?P<token>[\w-]+)/$",
            UnsubscribeDripView.as_view(),
            name="unsubscribe_drip",
        ),
    ]
