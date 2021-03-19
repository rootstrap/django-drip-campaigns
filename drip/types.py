"""Defines the types to be used within
the type annotations all along the system"""
from typing import Iterable, TypeVar

from datetime import datetime, timedelta
from django.db.models import F


AbstractQuerySetRule = TypeVar('AbstractQuerySetRule')
AbstractQuerySetRuleQuerySet = Iterable[AbstractQuerySetRule]  # noqa: F821, E501,
DateTime = datetime
TimeDeltaOrStr = TypeVar('TimeDeltaOrStr', timedelta, str)
BoolOrStr = TypeVar('BoolOrStr', bool, str)
FExpressionOrStr = TypeVar('FExpressionOrStr', F, str)
