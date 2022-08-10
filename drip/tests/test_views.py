import pytest
from django.test import Client

from drip.models import Drip
from drip.tokens import EmailToken
from drip.utils import get_user_model, validate_path_existence
from drip.views import UnsubscribeDripView

pytestmark = pytest.mark.django_db

User = get_user_model()


class TestCaseViews:
    def setup_method(self, test_method):
        self.client = Client()
        self.model_drip = Drip.objects.create(
            name="A test drip",
            subject_template="HELLO {{ user.username }}",
            body_html_template="KETTEHS ROCK!",
        )
        self.user = User.objects.create(
            username="user_test",
            email="some_user@test.com",
        )
        self.context_keys = {
            "user",
            "drip",
        }

    def test_get_unsubscribe_drip_success(self):
        email_token = EmailToken(self.user)
        drip_uidb64, uidb64, token = email_token.get_uidb64_token(self.model_drip.pk)
        url_args = {"drip_uidb64": drip_uidb64, "uidb64": uidb64, "token": token}
        unsubscribe_link = validate_path_existence("unsubscribe_drip", url_args)
        assert unsubscribe_link
        response = self.client.get(unsubscribe_link)

        assert response.template_name == [UnsubscribeDripView.template_name]  # type: ignore
        assert response.status_code == 200
        context_data = response.context_data  # type: ignore
        assert self.context_keys.issubset(context_data)
        assert context_data.get("user", None) == self.user
        assert context_data.get("drip", None) == self.model_drip

    @pytest.mark.parametrize(
        "extra_drip_uidb64, extra_uidb64, extra_token, exists_drip, exists_user",
        (
            ("invalid", "", "", False, True),  # Invalid drip_uidb64
            ("", "invalid", "", True, False),  # Invalid uidb64
            ("", "", "invalid", True, False),  # Invalid token
            ("invalid", "invalid", "", False, False),  # Invalid drip_uidb64 and uidb64
            ("", "invalid", "invalid", True, False),  # Invalid uidb64 and token
            ("invalid", "", "invalid", False, False),  # Invalid drip_uidb64 and token
            ("invalid", "invalid", "invalid", False, False),  # All invalid
        ),
    )
    def test_get_unsubscribe_drip_invalid(
        self,
        extra_drip_uidb64: str,
        extra_uidb64: str,
        extra_token: str,
        exists_drip: bool,
        exists_user: bool,
    ):
        email_token = EmailToken(self.user)
        drip_uidb64, uidb64, token = email_token.get_uidb64_token(self.model_drip.pk)
        url_args = {
            "drip_uidb64": f"{drip_uidb64}{extra_drip_uidb64}",
            "uidb64": f"{uidb64}{extra_uidb64}",
            "token": f"{token}{extra_token}",
        }
        unsubscribe_link = validate_path_existence("unsubscribe_drip", url_args)
        assert unsubscribe_link
        response = self.client.get(unsubscribe_link)

        assert response.template_name == [UnsubscribeDripView.invalid_template_name]  # type: ignore
        assert response.status_code == 200
        context_data = response.context_data  # type: ignore
        assert self.context_keys.issubset(context_data)
        user_context = context_data.get("user", None)
        expected_user = self.user if exists_user else None
        assert user_context == expected_user
        drip_context = context_data.get("drip", None)
        expected_drip = self.model_drip if exists_drip else None
        assert drip_context == expected_drip

    def test_post_unsubscribe_drip_success(self):
        email_token = EmailToken(self.user)
        drip_uidb64, uidb64, token = email_token.get_uidb64_token(self.model_drip.pk)
        url_args = {"drip_uidb64": drip_uidb64, "uidb64": uidb64, "token": token}
        unsubscribe_link = validate_path_existence("unsubscribe_drip", url_args)
        assert unsubscribe_link
        response = self.client.post(unsubscribe_link)

        assert response.template_name == [UnsubscribeDripView.success_template_name]  # type: ignore
        assert response.status_code == 200
        context_data = response.context_data  # type: ignore
        assert self.context_keys.issubset(context_data)
        assert context_data.get("user", None) == self.user
        assert context_data.get("drip", None) == self.model_drip

        # It creates the unsubscribed users model
        self.model_drip.refresh_from_db()
        assert self.user in self.model_drip.unsubscribed_users.all()

    @pytest.mark.parametrize(
        "extra_drip_uidb64, extra_uidb64, extra_token, exists_drip, exists_user",
        (
            ("invalid", "", "", False, True),  # Invalid drip_uidb64
            ("", "invalid", "", True, False),  # Invalid uidb64
            ("", "", "invalid", True, False),  # Invalid token
            ("invalid", "invalid", "", False, False),  # Invalid drip_uidb64 and uidb64
            ("", "invalid", "invalid", True, False),  # Invalid uidb64 and token
            ("invalid", "", "invalid", False, False),  # Invalid drip_uidb64 and token
            ("invalid", "invalid", "invalid", False, False),  # All invalid
        ),
    )
    def test_post_unsubscribe_drip_invalid(
        self,
        extra_drip_uidb64: str,
        extra_uidb64: str,
        extra_token: str,
        exists_drip: bool,
        exists_user: bool,
    ):
        email_token = EmailToken(self.user)
        drip_uidb64, uidb64, token = email_token.get_uidb64_token(self.model_drip.pk)
        url_args = {
            "drip_uidb64": f"{drip_uidb64}{extra_drip_uidb64}",
            "uidb64": f"{uidb64}{extra_uidb64}",
            "token": f"{token}{extra_token}",
        }
        unsubscribe_link = validate_path_existence("unsubscribe_drip", url_args)
        assert unsubscribe_link
        response = self.client.get(unsubscribe_link)

        assert response.template_name == [UnsubscribeDripView.invalid_template_name]  # type: ignore
        assert response.status_code == 200
        context_data = response.context_data  # type: ignore
        assert self.context_keys.issubset(context_data)
        user_context = context_data.get("user", None)
        expected_user = self.user if exists_user else None
        assert user_context == expected_user
        drip_context = context_data.get("drip", None)
        expected_drip = self.model_drip if exists_drip else None
        assert drip_context == expected_drip

        # It DOES NOT creates the unsubscribed users model
        self.model_drip.refresh_from_db()
        assert self.user not in self.model_drip.unsubscribed_users.all()
