"""Defines the types to be used within
the type annotations all along the system"""
from datetime import timedelta
from typing import TypeVar, Union

from django.db.models import F, Field, ForeignKey, ManyToManyField, OneToOneField
from django.db.models.fields.related import ForeignObjectRel as RelatedObject

AbstractQuerySetRule = TypeVar("AbstractQuerySetRule")
TimeDeltaOrStr = Union[timedelta, str]
BoolOrStr = Union[bool, str]
FExpressionOrStr = Union[F, str]
FieldValue = Union[TimeDeltaOrStr, BoolOrStr, FExpressionOrStr]
FieldType = Union[Field, ForeignKey, OneToOneField, RelatedObject, ManyToManyField]
