"""Defines the types to be used within
the type annotations all along the system"""
from datetime import timedelta
from typing import TypeVar, Union

from django.db.models import F

AbstractQuerySetRule = TypeVar("AbstractQuerySetRule")
TimeDeltaOrStr = Union[timedelta, str]
BoolOrStr = Union[bool, str]
FExpressionOrStr = Union[F, str]
FieldValue = Union[TimeDeltaOrStr, BoolOrStr, FExpressionOrStr]
