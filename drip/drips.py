import functools
import logging
import operator
from collections import ChainMap
from datetime import datetime, timedelta
from functools import lru_cache
from importlib import import_module
from typing import Any, Dict, List, Optional, TypedDict, Union

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.db.models import Q
from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet
from django.template import Context, Template
from django.utils.html import strip_tags
from django.utils.safestring import SafeString
from typing_extensions import TypeAlias

from drip.exceptions import MessageClassNotFound
from drip.models import Drip, SentDrip
from drip.utils import build_now_from_timedelta, get_conditional_now, get_user_model

User = get_user_model()

conditional_now = get_conditional_now()


DEFAULT_DRIP_MESSAGE_CLASS = "drip.drips.DripMessage"


def configured_message_classes() -> ChainMap:
    """
    Returns a ChainMap (basically a dict), between default settings and
    settings.DRIP_MESSAGE_CLASSES which should be a dictionary of the form:

        { message_class_name: class_path }

    For example, if you define this at DRIP_MESSAGE_CLASSES:

        {
            'default': 'my.path.to.DripMessage',
            'my_other_class': 'my.other.path.to.DripMessage',
        }

    The returning value of this method would be:

        {
            'default': 'my.path.to.Drip',
            'my_other_class': 'my.other.path.to.DripMessage',
        }

    But, if you define this:

        {
            'my_other_class': 'my.other.path.to.DripMessage',
        }

    The returning value of this method would be:

        {
            'default': 'drip.drips.DripMessage',
            'my_other_class': 'my.other.path.to.DripMessage',
        }

    A 'default' key is added when it's not present on DRIP_MESSAGE_CLASSES.
    """
    default_config = {"default": DEFAULT_DRIP_MESSAGE_CLASS}
    user_defined_config = getattr(settings, "DRIP_MESSAGE_CLASSES", {})
    return ChainMap(user_defined_config, default_config)


@lru_cache()
def message_class_for(name: str) -> "DripMessage":
    """
    Given a class's path, returns a reference to it.
    Raises MessageClassNotFound exception if name is not present in
    the ChainMap produced by configured_message_classes.
    """
    try:
        path = configured_message_classes()[name]
    except KeyError:
        logging.error('Name "{}" not found in configured message classes.'.format(name))
        raise MessageClassNotFound() from None
    else:
        mod_name, klass_name = path.rsplit(".", 1)
        mod = import_module(mod_name)
        klass = getattr(mod, klass_name)
        return klass


class DripBaseParamsOptions(TypedDict):
    drip_model: "Drip"
    name: str
    now_shift_kwargs: Dict[str, Any]


class DripMessage(object):
    """
    Email message abstraction for manage message interactions, based on EmailMultiAlternatives.
    You can extend this manually overriding any method that you need.

    :param drip_base: DripBase object to build email
    :type drip_base: DripBase
    :param user: User to send email
    :type user: User
    """

    # Ignoring this line because mypy says User is not a valid type
    def __init__(self, drip_base: "DripBase", user: User):  # type: ignore
        self.drip_base = drip_base
        self.user: TypeAlias = user
        self._context: Optional[Context] = None
        self._subject: Optional[SafeString] = None
        self._body: Optional[SafeString] = None
        self._plain: str = ""
        self._message: Union[EmailMessage, EmailMultiAlternatives, None] = None

    @property
    def from_email(self) -> Optional[str]:
        return self.drip_base.from_email

    @property
    def from_email_name(self) -> Optional[str]:
        return self.drip_base.from_email_name

    @property
    def context(self) -> Context:
        if not self._context:
            self._context = Context({"user": self.user})
        return self._context

    @property
    def subject(self) -> SafeString:
        drip_subject: SafeString
        if not self._subject:
            drip_subject = Template(
                self.drip_base.subject_template,
            ).render(self.context)
            self._subject = drip_subject
        else:
            drip_subject = self._subject
        return drip_subject

    @property
    def body(self) -> SafeString:
        drip_body: SafeString
        if not self._body:
            drip_body = Template(
                self.drip_base.body_template,
            ).render(self.context)
            self._body = drip_body
        else:
            drip_body = self._body
        return drip_body

    @property
    def plain(self) -> str:
        if not self._plain:
            self._plain = strip_tags(self.body)
        return self._plain

    def get_from_(self) -> str:
        if self.drip_base.from_email_name:
            from_ = "{name} <{email}>".format(
                name=self.drip_base.from_email_name,
                email=self.drip_base.from_email,
            )
        else:
            from_ = self.drip_base.from_email
        return from_

    @property
    def message(self) -> Union[EmailMessage, EmailMultiAlternatives]:
        if not self._message:
            from_ = self.get_from_()

            self._message = EmailMultiAlternatives(
                self.subject,
                self.plain,
                from_,
                [self.user.email],
            )

            # check if there are html tags in the rendered template
            if len(self.plain) != len(self.body):
                self._message.attach_alternative(self.body, "text/html")
        return self._message


class DripBase(object):
    """
    A base object for defining a Drip.

    You can extend this manually, or you can create full querysets
    and templates from the admin.
    """

    #: needs a unique name
    name: str
    subject_template: str
    body_template: str
    from_email: str
    from_email_name: str

    def __init__(self, drip_model: Drip, *args, **kwargs):
        self.drip_model = drip_model

        self.name = kwargs.pop("name", None)
        self.from_email = kwargs.pop("from_email", None)
        self.from_email_name = kwargs.pop(
            "from_email_name",
            None,
        )
        self.subject_template = kwargs.pop(
            "subject_template",
            None,
        )
        self.body_template = kwargs.pop("body_template", None)

        if not self.name:
            raise AttributeError("You must define a name.")

        self.now_shift_kwargs = kwargs.get("now_shift_kwargs", {})

    #########################
    #   DATE MANIPULATION   #
    #########################

    def now(self) -> datetime:
        """
        This allows us to override what we consider "now", making it easy
        to build timelines of who gets what when.
        """
        return build_now_from_timedelta(self.now_shift_kwargs)

    def timedelta(self, *args, **kwargs) -> timedelta:
        """
        If needed, this allows us the ability
        to manipulate the slicing of time.
        """
        return timedelta(*args, **kwargs)

    def walk(self, into_past: int = 0, into_future: int = 0) -> List["DripBase"]:
        """Walk over a date range and create
            new instances of self with new ranges.

        :param into_past: defaults to 0
        :type into_past: int, optional
        :param into_future: defaults to 0
        :type into_future: int, optional
        :return: List of DripBase instances.
        :rtype: List[DripBase]
        """
        walked_range = []
        for shift in range(-into_past, into_future):
            kwargs: DripBaseParamsOptions = dict(
                drip_model=self.drip_model,
                name=self.name,
                now_shift_kwargs={"days": shift},
            )
            walked_range.append(self.__class__(**kwargs))
        return walked_range

    def apply_queryset_rules(self, manager_qs: Union[BaseManager, QuerySet]) -> QuerySet:
        """First collect all filter/exclude kwargs and apply any annotations.
        Then apply all filters at once, and all excludes at once.

        :param manager_qs: Base queryset or manager to apply queryset rules
        :type manager_qs: Union[BaseManager, QuerySet]
        :return: Queryset with all (AND/OR) filters applied
        :rtype: QuerySet
        """
        return self.apply_and_queryset_rules(manager_qs) | self.apply_or_queryset_rules(manager_qs)

    def apply_or_queryset_rules(self, manager_qs: Union[BaseManager, QuerySet]) -> QuerySet:
        """First collect all filter kwargs. Then apply OR filters at once.

        :param manager_qs: Base queryset or manager to apply queryset rules
        :type manager_qs: Union[BaseManager, QuerySet]
        :return: Queryset with OR filters applied
        :rtype: QuerySet
        """
        rules: List[Q] = []
        rule_set = self.drip_model.queryset_rules.filter(rule_type="or")
        for query_rule in rule_set:
            kwargs = query_rule.filter_kwargs(now=self.now)
            query_or = Q(**kwargs)
            rules.append(query_or)

        query: Q = rules.pop() if rules else Q()
        for rule in rules:
            query |= rule
        qs = manager_qs.filter(query) if query != Q() else manager_qs.none()
        return qs

    def apply_and_queryset_rules(self, manager_qs: Union[BaseManager, QuerySet]) -> QuerySet:
        """First collect all filter/exclude kwargs and apply any annotations.
        Then apply AND filters at once, and all excludes at once.

        :param manager_qs: Base queryset or manager to apply queryset rules
        :type manager_qs: Union[BaseManager, QuerySet]
        :return: Queryset with AND filters applied
        :rtype: QuerySet
        """
        clauses: Dict[str, List] = {
            "filter": [],
            "exclude": [],
        }
        rules = []
        qs = manager_qs.all()
        for rule in self.drip_model.queryset_rules.filter(rule_type="and"):
            rules.append(rule)

            clause = clauses.get(rule.method_type, clauses["filter"])

            kwargs = rule.filter_kwargs(now=self.now)
            clause.append(Q(**kwargs))

            qs = rule.apply_any_annotation(qs)

        if clauses["exclude"]:
            qs = qs.exclude(functools.reduce(operator.or_, clauses["exclude"]))

        qs = qs.filter(*clauses["filter"]) if len(rules) > 0 else qs.none()

        return qs

    ##################
    #   MANAGEMENT   #
    ##################

    def get_queryset(self) -> QuerySet:
        """Apply queryset rules or returns the existing queryset

        :return: Queryset with all (AND/OR) filters applied
        :rtype: QuerySet
        """
        queryset = getattr(self, "_queryset", None)
        if queryset is None:
            self._queryset = self.apply_queryset_rules(
                self.queryset(),
            ).distinct()
        return self._queryset

    def run(self) -> Optional[int]:
        """Get the queryset, prune sent people, and send it.

        :return: Returns count of created SentDrips.
        :rtype: Optional[int]
        """
        if not self.drip_model.enabled:
            return None

        self.prune()
        count = self.send()

        return count

    def prune(self) -> None:
        """Do an exclude for all Users who have a SentDrip already."""
        target_user_ids = self.get_queryset().values_list("id", flat=True)
        exclude_user_ids = SentDrip.objects.filter(
            date__lt=conditional_now(),
            drip=self.drip_model,
            user__id__in=target_user_ids,
        ).values_list("user_id", flat=True)
        self._queryset = self.get_queryset().exclude(id__in=exclude_user_ids)

    def get_count_from_queryset(self, message_class) -> int:
        """
        Given a Message Class instance (by default drip.drips.DripMessage),
        returns the amount of sent Drips.
        """
        # TODO: try to reduce the side-effects of this method.
        count = 0
        for user in self.get_queryset():
            message_instance = message_class(self, user)
            try:
                result = message_instance.message.send()
                if result:
                    SentDrip.objects.create(
                        drip=self.drip_model,
                        user=user,
                        from_email=self.from_email,
                        from_email_name=self.from_email_name,
                        subject=message_instance.subject,
                        body=message_instance.body,
                    )
                    count += 1
            except Exception as e:
                logging.error(
                    "Failed to send drip {drip} to user {user}: {err}".format(
                        drip=self.drip_model.id,
                        user=str(user),
                        err=str(e),
                    )
                )
        return count

    def send(self) -> int:
        """
        Send the message to each user on the queryset.

        Create SentDrip for each user that gets a message.

        Returns count of created SentDrips.
        """

        if not self.from_email:
            self.from_email = getattr(
                settings,
                "DRIP_FROM_EMAIL",
                settings.DEFAULT_FROM_EMAIL,
            )
        MessageClass = message_class_for(self.drip_model.message_class)

        return self.get_count_from_queryset(MessageClass)

    ####################
    #   USER DEFINED   #
    ####################

    def queryset(self) -> BaseManager:
        """
        Returns a queryset of auth.User who meet the
        criteria of the drip.

        Alternatively, you could create Drips on the fly
        using a queryset builder from the admin interface...
        """
        User = get_user_model()
        return User.objects
