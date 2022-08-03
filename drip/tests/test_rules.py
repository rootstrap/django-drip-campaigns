from typing import Optional

import pytest
from django.core.exceptions import ValidationError
from faker import Faker

from drip.models import Drip, QuerySetRule
from drip.utils import get_simple_fields, get_user_model

pytestmark = pytest.mark.django_db


class TestCaseRules:
    faker: Faker

    @classmethod
    def setup_class(cls):
        cls.faker = Faker()

    def setup_method(self, test_method):
        self.drip = Drip.objects.create(
            name="A Drip just for Rules",
            subject_template="Hello",
            body_html_template="KETTEHS ROCK!",
        )

    def _get_field_value(self, field_type: str) -> Optional[str]:
        field_types = {
            "AutoField": self.faker.pyint(min_value=1),
            "CharField": self.faker.word(),
            "DateTimeField": f"now-{self.faker.pyint(min_value= 1, max_value=60)} days",
            "BooleanField": self.faker.pybool(),
            "EmailField": self.faker.email(),
            "TextField": self.faker.word(),
            "PositiveIntegerField": self.faker.pyint(min_value=1),
            "ForeignKey": self.faker.pyint(min_value=1),
            "OneToOneField": self.faker.pyint(min_value=1),
            "RelatedObject": self.faker.pyint(min_value=1),
            "ManyToManyField": self.faker.pyint(min_value=1),
        }
        field_value = field_types.get(field_type)
        return str(field_value) if field_value else None

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

    def test_drip_fields_validation_success(self):
        User = get_user_model()
        users_fields = get_simple_fields(User)
        # Using exact because it matches most of the field types
        lookup_type = "exact"
        for field in users_fields:
            field_name, field_type = field
            field_value = self._get_field_value(field_type)
            if field_value:
                rule = QuerySetRule(
                    drip=self.drip,
                    field_name=field_name,
                    lookup_type=lookup_type,
                    field_value=field_value,
                )
                rule.clean()
