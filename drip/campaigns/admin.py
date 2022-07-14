from collections import OrderedDict
from typing import Callable, List, Set, Union

from django.contrib import admin
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import URLPattern, path

from drip.models import Campaign, Drip
from drip.utils import get_user_model

User = get_user_model()


class DripInline(admin.TabularInline):
    model = Drip


class CampaignAdmin(admin.ModelAdmin):
    inlines = [
        DripInline,
    ]
    users_fields: Union[str, List[str]] = []

    def av(self, view: Callable) -> Callable:
        return self.admin_site.admin_view(view)

    def timeline(
        self,
        request: WSGIRequest,
        drip_id: int,
        into_past: int,
        into_future: int,
    ) -> HttpResponse:
        """
        Return a list of people who should get emails.
        """

        campaign = get_object_or_404(Campaign, id=drip_id)
        new_shifted_drips = OrderedDict()
        for shift in range(-into_past, into_future + 1):
            new_shifted_drips[shift] = {"drips": [], "now_shift_kwargs_days": shift}
        for drip in campaign.drip_set.all():
            seen_users: Set[int] = set()
            for shifted_drip in drip.drip.walk(into_past=int(into_past), into_future=int(into_future) + 1):
                shifted_drip.prune()
                shifted_data = {
                    "drip_model": drip,
                    "drip": shifted_drip,
                    "qs": shifted_drip.get_queryset().exclude(
                        id__in=seen_users,
                    ),
                }
                seen_users.update(shifted_drip.get_queryset().values_list("id", flat=True))
                shift_days = shifted_drip.now_shift_kwargs.get("days")
                if shift_days:
                    new_shifted_drips[shift_days]["drips"].append(shifted_data)  # type: ignore
                    new_shifted_drips[shift_days]["now"] = shifted_drip.now()

        return render(request, "campaign/timeline.html", locals())

    def get_urls(self) -> List[URLPattern]:
        urls = super(CampaignAdmin, self).get_urls()
        my_urls = [
            path(
                "<int:drip_id>/timeline/<int:into_past>/<int:into_future>/",
                self.av(self.timeline),
                name="campaign_drip_timeline",
            ),
        ]

        return my_urls + urls
