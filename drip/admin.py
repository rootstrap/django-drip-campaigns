import json

from django import forms
from django.contrib import admin
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.urls import path

from drip.models import Drip, SentDrip, QuerySetRule
from drip.drips import configured_message_classes, message_class_for
from drip.utils import get_user_model, get_simple_fields


class QuerySetRuleInline(admin.TabularInline):
    model = QuerySetRule


class DripForm(forms.ModelForm):
    message_class = forms.ChoiceField(
        choices=(
            (k, '{k} ({v})'.format(k=k, v=v))
            for k, v in configured_message_classes().items()
        ),
    )

    class Meta:
        model = Drip
        exclude = []


class DripAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled', 'message_class')
    inlines = [
        QuerySetRuleInline,
    ]
    form = DripForm
    users_fields = []

    def av(self, view):
        return self.admin_site.admin_view(view)

    def timeline(self, request, drip_id, into_past, into_future):
        """
        Return a list of people who should get emails.
        """

        drip = get_object_or_404(Drip, id=drip_id)

        shifted_drips = []
        seen_users = set()
        for shifted_drip in drip.drip.walk(
            into_past=int(into_past), into_future=int(into_future)+1
        ):
            shifted_drip.prune()
            shifted_drips.append(
                {
                    'drip': shifted_drip,
                    'qs': shifted_drip.get_queryset().exclude(
                        id__in=seen_users,
                    ),
                },
            )
            seen_users.update(
                shifted_drip.get_queryset().values_list('id', flat=True)
            )

        return render(request, 'drip/timeline.html', locals())

    def get_mime_html_from_alternatives(self, alternatives):
        html = ''
        mime = ''
        for body, mime in alternatives:
            if mime == 'text/html':
                html = body
                mime = 'text/html'
        return html, mime

    def get_mime_html(self, drip, user):
        drip_message = message_class_for(
            drip.message_class,
        )(drip.drip, user)
        if drip_message.message.alternatives:
            return self.get_mime_html_from_alternatives(
                drip_message.message.alternatives
            )
        html = drip_message.message.body
        mime = 'text/plain'
        return html, mime

    def view_drip_email(
        self, request, drip_id, into_past, into_future, user_id
    ):

        drip = get_object_or_404(Drip, id=drip_id)
        User = get_user_model()
        user = get_object_or_404(User, id=user_id)

        html, mime = self.get_mime_html(drip, user)

        return HttpResponse(html, content_type=mime)

    def build_extra_context(self, extra_context):
        extra_context = extra_context or {}
        User = get_user_model()
        if not self.users_fields:
            self.users_fields = json.dumps(get_simple_fields(User))
        extra_context['field_data'] = self.users_fields
        return extra_context

    def add_view(self, request, extra_context=None):
        return super(DripAdmin, self).add_view(
            request, extra_context=self.build_extra_context(extra_context),
        )

    def change_view(self, request, object_id, extra_context=None):
        return super(DripAdmin, self).change_view(
            request,
            object_id,
            extra_context=self.build_extra_context(extra_context)
        )

    def get_urls(self):
        urls = super(DripAdmin, self).get_urls()
        my_urls = [
            path(
                '<int:drip_id>/timeline/<int:into_past>/<int:into_future>/',
                self.av(self.timeline),
                name='drip_timeline'
            ),
            path(
                '<int:drip_id>/timeline/<int:into_past>/'
                '<int:into_future>/<int:user_id>/',
                self.av(self.view_drip_email),
                name='view_drip_email'
            )
        ]
        return my_urls + urls


admin.site.register(Drip, DripAdmin)


class SentDripAdmin(admin.ModelAdmin):
    list_display = [f.name for f in SentDrip._meta.fields]
    ordering = ['-id']


admin.site.register(SentDrip, SentDripAdmin)
