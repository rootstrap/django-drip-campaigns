from typing import Any, Dict, List

from django.views.generic import TemplateView

from drip.tokens import EmailToken


class UnsubscribeDripView(TemplateView):
    template_name = "unsubscribe_drip.html"
    invalid_template_name = "unsubscribe_drip_invalid.html"
    success_template_name = "unsubscribe_drip_success.html"

    def _set_user_and_drip(self, **kwargs: Any):
        drip_uidb64 = kwargs.get("drip_uidb64", "")
        uidb64 = kwargs.get("uidb64", "")
        token = kwargs.get("token", "")
        self.user = EmailToken.validate_user_uidb64_token(uidb64, token)
        self.drip = EmailToken.validate_drip_uidb64(drip_uidb64)
        self.post_sucess = False

    def dispatch(self, *args: Any, **kwargs: Any):
        self._set_user_and_drip(**kwargs)
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context_data = super().get_context_data(**kwargs)
        context_data["user"] = self.user
        context_data["drip"] = self.drip
        return context_data

    def get_template_names(self) -> List[str]:
        template_names = super().get_template_names()
        if not (self.user and self.drip):
            template_names = [self.invalid_template_name]
        if self.user and self.drip and self.post_sucess:
            template_names = [self.success_template_name]
        return template_names

    def post(self, *args: Any, **kwargs: Any):
        context = self.get_context_data(**kwargs)
        if self.user and self.drip:
            self.drip.unsubscribed_users.add(self.user.pk)
            self.post_sucess = True
        return self.render_to_response(context)


class UnsubscribeCampaignView(TemplateView):
    template_name = "unsubscribe_campaign.html"
    invalid_template_name = "unsubscribe_campaign_invalid.html"
    success_template_name = "unsubscribe_campaign_success.html"

    def _set_user_and_campaign(self, **kwargs):
        campaign_uidb64 = kwargs.get("campaign_uidb64", "")
        uidb64 = kwargs.get("uidb64", "")
        token = kwargs.get("token", "")
        self.user = EmailToken.validate_user_uidb64_token(uidb64, token)
        self.campaign = EmailToken.validate_campaign_uidb64(campaign_uidb64)
        self.post_sucess = False

    def dispatch(self, *args, **kwargs):
        self._set_user_and_campaign(**kwargs)
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context_data = super().get_context_data(**kwargs)
        context_data["user"] = self.user
        context_data["campaign"] = self.campaign
        return context_data

    def get_template_names(self) -> List[str]:
        template_names = super().get_template_names()
        if not (self.user and self.campaign):
            template_names = [self.invalid_template_name]
        if self.user and self.campaign and self.post_sucess:
            template_names = [self.success_template_name]
        return template_names

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if self.user and self.campaign:
            self.campaign.unsubscribed_users.add(self.user.pk)
            self.post_sucess = True
        return self.render_to_response(context)
