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

    @pytest.mark.parametrize(
        "field_name, lookup_type, field_value",
        (
            ("date__joined", "lte", "now-60 days"),  # test_bad_field_name
            ("date_joined", "lte", "now-2 months"),  # test_bad_field_value
        ),
    )
    def test_raise_errors(self, field_name: str, lookup_type: str, field_value: str):
        rule = QuerySetRule(
            drip=self.drip,
            field_name=field_name,
            lookup_type=lookup_type,
            field_value=field_value,
        )
        with pytest.raises(ValidationError):
            rule.clean()
