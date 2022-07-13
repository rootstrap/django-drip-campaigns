import random
from typing import Any, List

import pytest

from drip.models import Campaign, Drip
from drip.tests.factories import CampaignFactory, DripFactory

pytestmark = pytest.mark.django_db


def _drips_generator(amount: int, **drip_extra_args: Any) -> List[Campaign]:
    return DripFactory.create_batch(amount, **drip_extra_args)


class TestCaseCampaign:
    def test_campaings_creation(self):
        campaign = CampaignFactory()
        drip_count = random.randint(5, 15)
        _drips_generator(drip_count, campaign=campaign)

        assert len(campaign.drip_set.all()) == drip_count

    @pytest.mark.parametrize(
        ("delete_drips, drip_count, drip_count_after_delete"),
        (
            (True, 10, 0),
            (False, 10, 10),
        ),
    )
    def test_remove_campaings(
        self,
        delete_drips: bool,
        drip_count: int,
        drip_count_after_delete: int,
    ):
        campaign = CampaignFactory(delete_drips=delete_drips)
        _drips_generator(drip_count, campaign=campaign)

        campaign.delete()

        assert Drip.objects.count() == drip_count_after_delete
