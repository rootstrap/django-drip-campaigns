from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from campaigns.models import Campaign
from drip.models import Drip


class CampaignFactory(DjangoModelFactory):
    name = Faker("word")
    delete_drips = Faker("pybool")

    class Meta:
        model = Campaign


class DripFactory(DjangoModelFactory):
    name = Faker("word")
    campaign = SubFactory(CampaignFactory)

    class Meta:
        model = Drip
        django_get_or_create = ("name",)
