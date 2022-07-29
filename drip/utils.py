from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Type

import six
from django.contrib.auth.models import User
from django.db import models
from django.db.models import ForeignKey, ManyToManyField, OneToOneField
from django.db.models.fields.related import ForeignObjectRel as RelatedObject

from drip.scheduler.constants import VALID_SCHEDULERS, get_drip_scheduler_settings
from drip.types import FieldType

basestring = (str, bytes)
unicode = str


def check_redundant(model_stack: List[Type[models.Model]], stack_limit: int) -> bool:
    """
    Checks to ensure recursion isnt being redundant

    :param model_stack: List of models.Model
    :type model_stack: List[Type[models.Model]]
    :param stack_limit: recursion depth to check redundancy
    :type stack_limit: int
    :return: Bool that controls if stops recursion
    :rtype: bool
    """
    stop_recursion = False
    if len(model_stack) > stack_limit:
        # rudimentary CustomUser->User->CustomUser->User detection, or
        # stack depth shouldn't exceed x, or
        # we've hit a point where we are repeating models
        if (
            (model_stack[-3] == model_stack[-1])
            or (len(model_stack) > 5)
            or (len(set(model_stack)) != len(model_stack))
        ):
            stop_recursion = True
    return stop_recursion


def get_field_name(field, RelatedObject):
    field_name = field.name

    if isinstance(field, RelatedObject):
        field_name = field.field.related_query_name()
    return field_name


def get_full_field(parent_field: str, field_name: str) -> str:
    """
    :param parent_field: Name of parent field
    :type parent_field: str
    :param field_name: Field name
    :type field_name: str
    :return: It is the join between parent_field and field_name or just the field_name
    :rtype: str
    """
    if parent_field:
        full_field = "__".join([parent_field, field_name])
    else:
        full_field = field_name
    return full_field


def get_rel_model(field: FieldType, RelatedObject: RelatedObject) -> Type[models.Model]:
    if not is_valid_instance(field):  # type: ignore
        RelModel = field.model
        # field_names.extend(get_fields(RelModel, full_field, True))
    else:
        RelModel = field.related_model  # type: ignore
    return RelModel  # type: ignore


def is_valid_instance(field: FieldType) -> bool:
    return (
        isinstance(field, ForeignKey)
        or isinstance(field, OneToOneField)
        or isinstance(field, RelatedObject)
        or isinstance(field, ManyToManyField)
    )


def get_out_fields(
    Model: Type[models.Model],
    parent_field: str,
    model_stack: List[Type[models.Model]],
    excludes: List[str],
    fields: List[FieldType],
):
    out_fields = []
    for field in fields:

        field_name = get_field_name(field, RelatedObject)

        full_field = get_full_field(parent_field, field_name)

        if len([True for exclude in excludes if (exclude in full_field)]):
            continue

        # add to the list
        out_fields.append([full_field, field_name, Model, field.__class__])

        if is_valid_instance(field):

            RelModel = get_rel_model(field, RelatedObject)  # type: ignore

            out_fields.extend(
                get_fields(RelModel, full_field, list(model_stack)),
            )

    return out_fields


def get_fields(
    Model: Type[models.Model],
    parent_field: str = "",
    model_stack: List[Type[models.Model]] = [],
    stack_limit: int = 2,
    excludes: List[str] = ["permissions", "comment", "content_type"],
):
    """
    Given a Model, return a list of lists of strings with important stuff:
    ...
    ['test_user__user__customuser', 'customuser', 'User', 'RelatedObject']
    ['test_user__unique_id', 'unique_id', 'TestUser', 'CharField']
    ['test_user__confirmed', 'confirmed', 'TestUser', 'BooleanField']
    ...

    """

    # github.com/omab/python-social-auth/commit/d8637cec02422374e4102231488481170dc51057
    if isinstance(Model, six.string_types):
        app_label, model_name = Model.split(".")
        Model = models.get_model(app_label, model_name)  # type: ignore

    fields = Model._meta.fields + Model._meta.many_to_many + Model._meta.get_fields()  # type: ignore
    model_stack.append(Model)

    # do a variety of checks to ensure recursion isnt being redundant

    stop_recursion = check_redundant(model_stack, stack_limit)

    if stop_recursion:
        return []  # give empty list for "extend"

    return get_out_fields(Model, parent_field, model_stack, excludes, fields)


def give_model_field(full_field: str, Model: Type[models.Model]) -> tuple:
    """Given a field_name and Model:

    "test_user__unique_id", <AchievedGoal>

    Returns "test_user__unique_id", "id", <Model>, <ModelField>

    :param full_field: full field name
    :type full_field: str
    :param Model: models.Model
    :type Model: models.Model
    :raises Exception: If the key is not found it raises and exception
    :return: It is a tuple with field full name, field name, <Model>, <ModelField>
    :rtype: tuple
    """

    field_data = get_fields(Model, "", [])

    for full_key, name, _Model, _ModelField in field_data:
        if full_key == full_field:
            return full_key, name, _Model, _ModelField
    message_exception = "Field key `{field}` not found on `{model}`.".format(
        field=full_field,
        model=Model.__name__,  # type: ignore
    )
    raise Exception(message_exception)


def get_simple_fields(Model: Type[models.Model], **kwargs) -> List:
    ret_list: List = []
    for f in get_fields(Model, **kwargs):
        if f[0] not in [x[0] for x in ret_list]:
            # Add field if not already in list
            ret_list.append([f[0], f[3].__name__])
    return ret_list


def get_user_model() -> Type[User]:
    # handle 1.7 and back
    try:
        from django.contrib.auth import get_user_model as django_get_user_model

        User = django_get_user_model()
    except ImportError:
        pass
    return User


def get_conditional_now() -> Callable:
    # handle now import for appropiate django version
    try:
        from django.utils.timezone import now as conditional_now
    except ImportError:
        conditional_now = datetime.now
    return conditional_now


def build_now_from_timedelta(now_shift_kwargs: Dict[str, Any]) -> datetime:
    """
    Build "now" from shift timedelta.
    """
    conditional_now = get_conditional_now()
    return conditional_now() + timedelta(**now_shift_kwargs)


class DripScheduleSettingsError(Exception):
    pass


def validate_schedules():
    _, _, _, _, SCHEDULER = get_drip_scheduler_settings()
    if SCHEDULER not in VALID_SCHEDULERS:
        raise DripScheduleSettingsError(f"{SCHEDULER} is not a valid SCHEDULER configuration")
