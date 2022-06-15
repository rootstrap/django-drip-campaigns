from django.core.exceptions import ValidationError
from django.test import TestCase

from drip.models import Drip, QuerySetRule


class RulesTestCase(TestCase):
    def setUp(self):
        self.drip = Drip.objects.create(
            name="A Drip just for Rules",
            subject_template="Hello",
            body_html_template="KETTEHS ROCK!",
        )

    def test_valid_rule(self):
        rule = QuerySetRule(
            drip=self.drip,
            field_name="date_joined",
            lookup_type="lte",
            field_value="now-60 days",
        )
        rule.clean()

    def test_bad_field_name(self):
        rule = QuerySetRule(
            drip=self.drip,
            field_name="date__joined",
            lookup_type="lte",
            field_value="now-60 days",
        )
        self.assertRaises(ValidationError, rule.clean)

    def test_bad_field_value(self):
        rule = QuerySetRule(
            drip=self.drip,
            field_name="date_joined",
            lookup_type="lte",
            field_value="now-2 months",
        )
        self.assertRaises(ValidationError, rule.clean)
