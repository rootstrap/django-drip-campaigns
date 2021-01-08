from django.test import TestCase
from drip.models import Drip
from campaigns.models import Campaign

DRIP_AMOUNT = 10


def _drips_generator(amount, **drip_extra_args):
    for i in range(amount):
        yield Drip(
            name='{}th drip'.format(i),
            **drip_extra_args
        )


class DripsTestCase(TestCase):

    def test_campaings_creation(self):
        campaign = Campaign()
        campaign.save()

        Drip.objects.bulk_create(
            _drips_generator(
                DRIP_AMOUNT,
                campaign=campaign
            )
        )

        assert len(campaign.drip_set.all()) == DRIP_AMOUNT

    def test_remove_campaings(self):
        campaign_delete_drips = Campaign(name='remove me!', delete_drips=True)
        campaign_delete_drips.save()

        Drip.objects.bulk_create(
            _drips_generator(
                DRIP_AMOUNT,
                campaign=campaign_delete_drips
            )
        )

        drips_before_delete = Drip.objects.count()

        campaign_delete_drips.delete()

        assert drips_before_delete > Drip.objects.count()

        campaign_do_not_delete_drips = Campaign(
            name='remove me, but keep my drips alive!',
            delete_drips=False,
        )
        campaign_do_not_delete_drips.save()

        Drip.objects.bulk_create(
            _drips_generator(
                DRIP_AMOUNT,
                campaign=campaign_do_not_delete_drips
            )
        )

        drips_before_delete = Drip.objects.count()

        campaign_do_not_delete_drips.delete()

        assert drips_before_delete == Drip.objects.count()
