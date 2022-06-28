from typing import Any, Dict, Optional, Type

import pytest
from django.conf import settings
from django.core import mail

from drip.drips import DripMessage
from drip.models import Drip, QuerySetRule
from drip.utils import get_user_model

pytestmark = pytest.mark.django_db
User = get_user_model()


# Used by CustomMessagesTest
class PlainDripEmail(DripMessage):
    @property
    def message(self):
        if not self._message:
            email = mail.EmailMessage(
                self.subject,
                self.plain,
                self.from_email,
                [self.user.email],
            )
            self._message = email
        return self._message


class TestCustomMessages:
    old_msg_classes: Optional[str]

    @classmethod
    def setup_class(cls):
        cls.old_msg_classes = getattr(settings, "DRIP_MESSAGE_CLASSES", None)

    def setup_method(self, test_method):
        self.user = User.objects.create(
            username="customuser",
            email="custom@example.com",
        )
        self.model_drip = Drip.objects.create(
            name="A Custom Week Ago",
            subject_template="HELLO {{ user.username }}",
            body_html_template="<h2>This</h2> is an <b>example</b>" " html <strong>body</strong>.",
        )
        QuerySetRule.objects.create(
            drip=self.model_drip,
            field_name="id",
            lookup_type="exact",
            field_value=self.user.id,
        )

    @pytest.mark.parametrize(
        "settings_message_config, message_class, expected_result, len_mail, mail_instance",
        (
            (None, None, 1, 1, mail.EmailMultiAlternatives),  # test_default_email
            (
                {"plain": "drip.tests.PlainDripEmail"},
                None,
                1,
                1,
                mail.EmailMultiAlternatives,  # Since we did not specify custom class, default should be used.
            ),  # test_custom_added_not_used
            (
                {
                    "plain": "drip.tests.test_custom_messages.PlainDripEmail",
                },
                "plain",
                1,
                1,
                mail.EmailMessage,  # In this case we did specify the custom key, so message should be of custom type.
            ),  # test_custom_added_and_used
            (
                {
                    "default": "drip.tests.test_custom_messages.PlainDripEmail",
                },
                None,
                1,
                1,
                mail.EmailMessage,
            ),  # test_override_default
        ),
    )
    def test_emails(
        self,
        settings_message_config: Optional[Dict[str, Any]],
        message_class: Optional[str],
        expected_result: int,
        len_mail: int,
        mail_instance: Type[mail.EmailMessage],
    ):
        if settings_message_config:
            settings.DRIP_MESSAGE_CLASSES = settings_message_config
        if message_class:
            self.model_drip.message_class = message_class
            self.model_drip.save()
        result = self.model_drip.drip.send()

        assert expected_result == result
        assert len_mail == len(mail.outbox)

        email = mail.outbox.pop()
        assert isinstance(email, mail_instance)
