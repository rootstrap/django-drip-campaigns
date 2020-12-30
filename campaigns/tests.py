from django.test import TestCase
from drip.models import Drip
from campaigns.models import Campaign

DRIP_AMOUNT = 10


class DripsTestCase(TestCase):

    def test_campaings_creation(self):
        campaign = Campaign()
        campaign.save()
        drips = [Drip(name='{}th drip'.format(i), campaign=campaign) for i in range(DRIP_AMOUNT)]
        Drip.objects.bulk_create(drips)

        assert len(campaign.drip_set.all()) == DRIP_AMOUNT
