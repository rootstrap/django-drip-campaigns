from typing import Any, Dict, List

from django.shortcuts import render
from django.views.generic import TemplateView

from drip.tokens import EmailToken


class UnsubscribeDripView(TemplateView):
    template_name = "unsubscribe_drip.html"
    invalid_template_name = "unsubscribe_drip_invalid.html"
    success_template_name = "unsubscribe_drip_success.html"

    def _set_user_and_drip(self, **kwargs):
        drip_uidb64 = kwargs.get("drip_uidb64", "")
        uidb64 = kwargs.get("uidb64", "")
        token = kwargs.get("token", "")
        self.user = EmailToken.validate_user_uidb64_token(uidb64, token)
        self.drip = EmailToken.validate_drip_uidb64(drip_uidb64)

    def dispatch(self, *args, **kwargs):
        self._set_user_and_drip(**kwargs)
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context_data = super().get_context_data(**kwargs)
        context_data["user"] = self.user
        return context_data

    def get_template_names(self) -> List[str]:
        template_names = super().get_template_names()
        if not (self.user and self.drip):
            template_names = [self.invalid_template_name]
        return template_names

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if self.user and self.drip:
            self.drip.unsubscribed_users.add(self.user.pk)
            return render(request, self.success_template_name, context)
        return self.render_to_response(context)
