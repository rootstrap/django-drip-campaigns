from datetime import datetime
from typing import TYPE_CHECKING, Callable, Dict, Union

if TYPE_CHECKING:
    from drip.drips import DripBase

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.query import QuerySet

from drip.campaigns.models import Campaign
from drip.helpers import parse
from drip.types import BoolOrStr, FExpressionOrStr, FieldValue, TimeDeltaOrStr
from drip.utils import get_user_model, validate_schedules

# Raise exception if SCHEDULER is not valid
validate_schedules()

# from drip.helpers import parse.
# just using this to parse, but totally insane package naming...
# https://bitbucket.org/schinckel/django-timedelta-field/


class AbstractDrip(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    lastchanged = models.DateTimeField(auto_now=True)
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Drip Name",
        help_text="A unique name for this drip.",
    )
    enabled = models.BooleanField(default=False)

    from_email = models.EmailField(null=True, blank=True, help_text="Set a custom from email.")
    from_email_name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Set a name for a custom from email.",
    )
    subject_template = models.TextField(null=True, blank=True)
    body_html_template = models.TextField(
        null=True,
        blank=True,
        help_text="You will have settings and user in the context.",
    )
    message_class = models.CharField(max_length=120, blank=True, default="default")

    campaign = models.ForeignKey(
        Campaign,
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_DEFAULT,
        help_text="If set, this is the campaign to which this Drip belongs to.",
    )

    class Meta:
        abstract = True

    @property
    def drip(self) -> "DripBase":
        from drip.drips import DripBase

        # Ignoring this line because we are using AbstractDrip here
        drip = DripBase(
            drip_model=self,  # type: ignore
            name=self.name,
            from_email=self.from_email if self.from_email else None,
            from_email_name=self.from_email_name if (self.from_email_name) else None,
            subject_template=self.subject_template if (self.subject_template) else None,
            body_template=self.body_html_template if (self.body_html_template) else None,
        )
        return drip

    def __str__(self) -> str:
        return self.name


class Drip(AbstractDrip):
    pass


class AbstractSentDrip(models.Model):
    """
    Keeps a record of all sent drips.
    """

    date = models.DateTimeField(auto_now_add=True)
    drip = models.ForeignKey(
        "drip.Drip",
        related_name="sent_drips",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        getattr(settings, "AUTH_USER_MODEL", "auth.User"),
        related_name="sent_drips",
        on_delete=models.CASCADE,
    )
    subject = models.TextField()
    body = models.TextField()
    from_email = models.EmailField(
        # For south so that it can migrate existing rows.
        null=True,
        default=None,
    )
    from_email_name = models.CharField(
        max_length=150,
        # For south so that it can migrate existing rows.
        null=True,
        default=None,
    )

    class Meta:
        abstract = True


class SentDrip(AbstractSentDrip):
    pass


METHOD_TYPES = (
    ("filter", "Filter"),
    ("exclude", "Exclude"),
)

LOOKUP_TYPES = (
    ("exact", "exactly"),
    ("iexact", "exactly (case insensitive)"),
    ("contains", "contains"),
    ("icontains", "contains (case insensitive)"),
    ("regex", "regex"),
    ("iregex", "regex (case insensitive)"),
    ("gt", "greater than"),
    ("gte", "greater than or equal to"),
    ("lt", "less than"),
    ("lte", "less than or equal to"),
    ("startswith", "starts with"),
    ("endswith", "ends with"),
    ("istartswith", "starts with (case insensitive)"),
    ("iendswith", "ends with (case insensitive)"),
)

RULE_TYPES = (
    ("or", "Or"),
    ("and", "And"),
)


class AbstractQuerySetRule(models.Model):
    """
    Allows to apply filters to drips
    """

    date = models.DateTimeField(auto_now_add=True)
    lastchanged = models.DateTimeField(auto_now=True)

    drip = models.ForeignKey(
        Drip,
        related_name="queryset_rules",
        on_delete=models.CASCADE,
    )

    method_type = models.CharField(
        max_length=12,
        default="filter",
        choices=METHOD_TYPES,
    )
    field_name = models.CharField(max_length=128, verbose_name="Field name of User")
    lookup_type = models.CharField(max_length=12, default="exact", choices=LOOKUP_TYPES)
    rule_type = models.CharField(max_length=3, default="and", choices=RULE_TYPES)

    field_value = models.CharField(
        max_length=255,
        help_text=(
            "Can be anything from a number, to a string. Or, do "
            + "`now-7 days` or `today+3 days` for fancy timedelta."
        ),
    )

    def clean(self) -> None:
        User = get_user_model()
        try:
            self.apply(User.objects.all())
        except Exception as e:
            raise ValidationError(
                "{type_name} raised trying to apply rule: {error}".format(
                    type_name=type(e).__name__,
                    error=str(e),
                )
            )

    @property
    def annotated_field_name(self) -> str:
        """
        Generates an annotated version of this field's name,
        based on self.field_name
        """
        field_name = self.field_name
        if field_name.endswith("__count"):
            agg, _, _ = field_name.rpartition("__")
            field_name = "num_{agg}".format(agg=agg.replace("__", "_"))

        return field_name

    def apply_any_annotation(self, qs: QuerySet) -> QuerySet:
        """
        Returns qs annotated with Count over this field's name.
        """
        if self.field_name.endswith("__count"):
            field_name = self.annotated_field_name
            agg, _, _ = self.field_name.rpartition("__")
            qs = qs.annotate(**{field_name: models.Count(agg, distinct=True)})
        return qs

    def set_time_deltas_and_dates(self, now: Callable, field_value: str) -> TimeDeltaOrStr:
        """
        Parses the field_value parameter and returns a TimeDelta object
        The field_value string might start with one of
        the following substrings:
        * "now-"
        * "now+"
        * "today-"
        * "today+"
        Otherwise returns field_value unchanged.
        """
        time_delta_value: TimeDeltaOrStr = field_value
        # set time deltas and dates
        if self.field_value.startswith("now-"):
            field_value = self.field_value.replace("now-", "")
            time_delta_value = now() - parse(field_value)
        elif self.field_value.startswith("now+"):
            field_value = self.field_value.replace("now+", "")
            time_delta_value = now() + parse(field_value)
        elif self.field_value.startswith("today-"):
            field_value = self.field_value.replace("today-", "")
            time_delta_value = now().date() - parse(field_value)
        elif self.field_value.startswith("today+"):
            field_value = self.field_value.replace("today+", "")
            time_delta_value = now().date() + parse(field_value)
        return time_delta_value

    def set_f_expressions(self, field_value: str) -> FExpressionOrStr:
        """
        If field_value starts with the substring 'F\_', returns an instance
        of models.F within the field_value expression, otherwise returns
        field_value unchanged.
        """  # noqa: W605
        # F expressions
        f_expr: FExpressionOrStr = field_value
        if self.field_value.startswith("F_"):
            field_value = self.field_value.replace("F_", "")
            f_expr = models.F(field_value)
        return f_expr

    def set_booleans(self, field_value: str) -> BoolOrStr:
        """
        Returns True or False whether field value is 'True' or
        'False' respectively.
        Otherwise returns field_value unchanged.
        """
        # set booleans
        booleans: BoolOrStr = field_value
        if self.field_value == "True":
            booleans = True
        if self.field_value == "False":
            booleans = False
        return booleans

    def filter_kwargs(
        self, now: Callable = datetime.now
    ) -> Dict[str, Union[BoolOrStr, FExpressionOrStr, TimeDeltaOrStr]]:
        """
        Returns a dictionary {field_name: field_value} where:

        - field_name is self.annotated_field_name in addition to
          self.lookup_type in the form FIELD_NAME__LOOKUP.
        - field_value is the result of passing self.field_value
          through parsing methods.

        The resulting dict can be used to apply filters over querysets.

        .. code-block:: python

          queryset.filter(**obj.filter_kwargs(datetime.now()))

        """
        # Support Count() as m2m__count
        field_name = self.annotated_field_name
        field_name = "__".join([field_name, self.lookup_type])

        field_value: FieldValue = self.set_time_deltas_and_dates(now, self.field_value)

        field_value = self.set_f_expressions(field_value) if type(field_value) == str else field_value

        field_value = self.set_booleans(field_value) if type(field_value) == str else field_value

        kwargs = {field_name: field_value}

        return kwargs

    def apply(self, qs: QuerySet, now: Callable = datetime.now) -> QuerySet:
        """
        Returns ``qs`` filtered/excluded by any filter resulting
        from ``self.filter_kwargs`` depending on whether
        ``self.method_type`` is one of the following:

        - "filter"
        - "exclude"

        Also annotates ``qs`` by calling ``self.apply_any_annotation``.
        """
        kwargs = self.filter_kwargs(now)
        qs = self.apply_any_annotation(qs)

        if self.method_type == "filter":
            return qs.filter(**kwargs)
        elif self.method_type == "exclude":
            return qs.exclude(**kwargs)

        # catch as default
        return qs.filter(**kwargs)

    class Meta:
        abstract = True


class QuerySetRule(AbstractQuerySetRule):
    pass


class TestUserUUIDModel(models.Model):
    """
    Class to test UUID field as id in User model
    """

    id = models.UUIDField(primary_key=True)
