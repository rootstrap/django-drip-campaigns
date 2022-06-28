import pytest
from django.core.exceptions import ValidationError

from drip.models import Drip, QuerySetRule

pytestmark = pytest.mark.django_db


class TestCaseRules:
    def setup_method(self, test_method):
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
        with pytest.raises(ValidationError):
            rule.clean()

    def test_bad_field_value(self):
        rule = QuerySetRule(
            drip=self.drip,
            field_name="date_joined",
            lookup_type="lte",
            field_value="now-2 months",
        )
        with pytest.raises(ValidationError):
            rule.clean()
