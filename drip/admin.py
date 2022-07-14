import json
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from django import forms
from django.contrib import admin
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import URLPattern, path

from drip.campaigns.admin import CampaignAdmin
from drip.drips import configured_message_classes, message_class_for
from drip.models import Campaign, Drip, QuerySetRule, SentDrip
from drip.utils import get_simple_fields, get_user_model

User = get_user_model()


class QuerySetRuleInline(admin.TabularInline):
    model = QuerySetRule


class DripForm(forms.ModelForm):
    message_class = forms.ChoiceField(
        choices=((k, "{k} ({v})".format(k=k, v=v)) for k, v in configured_message_classes().items()),
    )

    class Meta:
        model = Drip
        exclude: List[str] = []


class DripAdmin(admin.ModelAdmin):
    list_display = ("name", "enabled", "message_class")
    inlines = [
        QuerySetRuleInline,
    ]
    form = DripForm
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

        drip = get_object_or_404(Drip, id=drip_id)

        shifted_drips = []
        seen_users: Set[int] = set()
        for shifted_drip in drip.drip.walk(into_past=int(into_past), into_future=int(into_future) + 1):
            shifted_drip.prune()
            shifted_drips.append(
                {
                    "drip": shifted_drip,
                    "qs": shifted_drip.get_queryset().exclude(
                        id__in=seen_users,
                    ),
                },
            )
            seen_users.update(shifted_drip.get_queryset().values_list("id", flat=True))

        return render(request, "drip/timeline.html", locals())

    def get_mime_html_from_alternatives(self, alternatives: List[Tuple[str, str]]) -> Tuple[str, str]:
        html = ""
        mime = ""
        for body, mime in alternatives:
            if mime == "text/html":
                html = body
                mime = "text/html"
        return html, mime

    # Ignoring this line because mypy says User is not a valid type
    def get_mime_html(self, drip: Drip, user: User) -> Tuple[str, str]:  # type: ignore
        # Ignoring this line because mypy says DripMessage is not callable
        drip_message = message_class_for(  # type: ignore
            drip.message_class,
        )(drip.drip, user)
        if drip_message.message.alternatives:
            return self.get_mime_html_from_alternatives(drip_message.message.alternatives)
        html = drip_message.message.body
        mime = "text/plain"
        return html, mime

    def view_drip_email(
        self,
        request: WSGIRequest,
        drip_id: int,
        into_past: int,
        into_future: int,
        user_id: int,
    ) -> HttpResponse:
        drip = get_object_or_404(Drip, id=drip_id)
        user = get_object_or_404(User, id=user_id)

        html, mime = self.get_mime_html(drip, user)

        return HttpResponse(html, content_type=mime)

    def build_extra_context(self, extra_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        extra_context = extra_context or {}
        User = get_user_model()
        if not self.users_fields:
            self.users_fields = json.dumps(get_simple_fields(User))
        extra_context["field_data"] = self.users_fields
        return extra_context

    def add_view(self, request: HttpRequest, form_url: str = "", extra_context: Any = None) -> HttpResponse:
        return super(DripAdmin, self).add_view(
            request,
            form_url=form_url,
            extra_context=self.build_extra_context(extra_context),  # type: ignore
        )

    def change_view(self, request: HttpRequest, object_id: str, form_url="", extra_context: Any = None) -> HttpResponse:
        return super(DripAdmin, self).change_view(
            request, object_id, form_url=form_url, extra_context=self.build_extra_context(extra_context)
        )

    def get_urls(self) -> List[URLPattern]:
        urls = super(DripAdmin, self).get_urls()
        my_urls = [
            path(
                "<int:drip_id>/timeline/<int:into_past>/<int:into_future>/",
                self.av(self.timeline),
                name="drip_timeline",
            ),
        ]

        User = get_user_model()
        if User._meta.get_field("id").get_internal_type() == "UUIDField":
            my_urls += [
                path(
                    "<int:drip_id>/timeline/<int:into_past>/<int:into_future>/<uuid:user_id>/",  # noqa
                    self.av(self.view_drip_email),
                    name="view_drip_email",
                ),
            ]
        else:
            my_urls += [
                path(
                    "<int:drip_id>/timeline/<int:into_past>/<int:into_future>/<int:user_id>/",  # noqa
                    self.av(self.view_drip_email),
                    name="view_drip_email",
                ),
            ]

        return my_urls + urls


admin.site.register(Drip, DripAdmin)


class SentDripAdmin(admin.ModelAdmin):
    list_display = [f.name for f in SentDrip._meta.fields]
    ordering = ["-id"]


admin.site.register(SentDrip, SentDripAdmin)


admin.site.register(Campaign, CampaignAdmin)
