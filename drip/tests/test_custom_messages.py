from django.conf import settings
from django.core import mail
from django.test import TestCase

from drip.drips import DripMessage
from drip.models import Drip, QuerySetRule
from drip.utils import get_user_model


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


class CustomMessagesTest(TestCase):
    def setUp(self):
        self.User = get_user_model()

        self.old_msg_classes = getattr(settings, "DRIP_MESSAGE_CLASSES", None)
        self.user = self.User.objects.create(
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

    def test_default_email(self):
        result = self.model_drip.drip.send()
        self.assertEqual(1, result)
        self.assertEqual(1, len(mail.outbox))
        email = mail.outbox.pop()
        self.assertIsInstance(email, mail.EmailMultiAlternatives)

    def test_custom_added_not_used(self):
        settings.DRIP_MESSAGE_CLASSES = {"plain": "drip.tests.PlainDripEmail"}
        result = self.model_drip.drip.send()
        self.assertEqual(1, result)
        self.assertEqual(1, len(mail.outbox))
        email = mail.outbox.pop()
        # Since we did not specify custom class, default should be used.
        self.assertIsInstance(email, mail.EmailMultiAlternatives)

    def test_custom_added_and_used(self):
        settings.DRIP_MESSAGE_CLASSES = {
            "plain": "drip.tests.test_custom_messages.PlainDripEmail",
        }
        self.model_drip.message_class = "plain"
        self.model_drip.save()
        result = self.model_drip.drip.send()
        self.assertEqual(1, result)
        self.assertEqual(1, len(mail.outbox))
        email = mail.outbox.pop()
        # In this case we did specify the custom key,
        # so message should be of custom type.
        self.assertIsInstance(email, mail.EmailMessage)

    def test_override_default(self):
        settings.DRIP_MESSAGE_CLASSES = {
            "default": "drip.tests.test_custom_messages.PlainDripEmail",
        }
        result = self.model_drip.drip.send()
        self.assertEqual(1, result)
        self.assertEqual(1, len(mail.outbox))
        email = mail.outbox.pop()
        self.assertIsInstance(email, mail.EmailMessage)
