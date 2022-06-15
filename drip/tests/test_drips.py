from datetime import timedelta
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import resolve, reverse
from django.utils import timezone

from credits.models import Profile
from drip.admin import DripAdmin
from drip.drips import DripBase
from drip.models import Drip, QuerySetRule, SentDrip
from drip.utils import get_user_model, unicode


def get_user_model_mock():
    from drip.models import TestUserUUIDModel

    return TestUserUUIDModel


class DripsTestCase(TestCase):
    def setUp(self):
        """
        Creates 20 users, half of which buy 25 credits a day,
        and the other half that does none.
        """
        self.User = get_user_model()

        start = timezone.now() - timedelta(hours=2)
        num_string = [
            "first",
            "second",
            "third",
            "fourth",
            "fifth",
            "sixth",
            "seventh",
            "eighth",
            "ninth",
            "tenth",
        ]

        for i, name in enumerate(num_string):
            user = self.User.objects.create(
                username="{name}_25_credits_a_day".format(name=name),
                email="{name}@test.com".format(name=name),
            )
            self.User.objects.filter(id=user.id).update(
                date_joined=start - timedelta(days=i),
            )

            profile = Profile.objects.get(user=user)
            profile.credits = i * 25
            profile.save()

        for i, name in enumerate(num_string):
            user = self.User.objects.create(
                username="{name}_no_credits".format(name=name),
                email="{name}@test.com".format(name=name),
            )
            self.User.objects.filter(id=user.id).update(
                date_joined=start - timedelta(days=i),
            )

    def test_users_exists(self):
        self.assertEqual(20, self.User.objects.all().count())

    def test_day_zero_users(self):
        start = timezone.now() - timedelta(days=1)
        end = timezone.now()
        self.assertEqual(
            2,
            self.User.objects.filter(
                date_joined__range=(start, end),
            ).count(),
        )

    def test_day_two_users_active(self):
        start = timezone.now() - timedelta(days=3)
        end = timezone.now() - timedelta(days=2)
        self.assertEqual(
            1,
            self.User.objects.filter(
                date_joined__range=(start, end),
                profile__credits__gt=0,
            ).count(),
        )

    def test_day_two_users_inactive(self):
        start = timezone.now() - timedelta(days=3)
        end = timezone.now() - timedelta(days=2)
        self.assertEqual(
            1,
            self.User.objects.filter(
                date_joined__range=(start, end),
                profile__credits=0,
            ).count(),
        )

    def test_day_seven_users_active(self):
        start = timezone.now() - timedelta(days=8)
        end = timezone.now() - timedelta(days=7)
        self.assertEqual(
            1,
            self.User.objects.filter(
                date_joined__range=(start, end),
                profile__credits__gt=0,
            ).count(),
        )

    def test_day_seven_users_inactive(self):
        start = timezone.now() - timedelta(days=8)
        end = timezone.now() - timedelta(days=7)
        self.assertEqual(
            1,
            self.User.objects.filter(
                date_joined__range=(start, end),
                profile__credits=0,
            ).count(),
        )

    def test_day_fourteen_users_active(self):
        start = timezone.now() - timedelta(days=15)
        end = timezone.now() - timedelta(days=14)
        self.assertEqual(
            0,
            self.User.objects.filter(
                date_joined__range=(start, end),
                profile__credits__gt=0,
            ).count(),
        )

    def test_day_fourteen_users_inactive(self):
        start = timezone.now() - timedelta(days=15)
        end = timezone.now() - timedelta(days=14)
        self.assertEqual(
            0,
            self.User.objects.filter(
                date_joined__range=(start, end),
                profile__credits=0,
            ).count(),
        )

    ########################
    #   RELATION SNAGGER   #
    ########################

    def test_get_simple_fields(self):
        from drip.utils import get_simple_fields

        simple_fields = get_simple_fields(self.User)
        self.assertTrue(
            bool([sf for sf in simple_fields if "profile" in sf[0]]),
        )

    ##################
    #   TEST DRIPS   #
    ##################

    def test_backwards_drip_class(self):
        for drip in Drip.objects.all():
            self.assertTrue(issubclass(drip.drip.__class__, DripBase))

    def build_joined_date_drip(self, shift_one=7, shift_two=8):
        model_drip = Drip.objects.create(
            name="A Custom Week Ago",
            subject_template="HELLO {{ user.username }}",
            body_html_template="KETTEHS ROCK!",
        )
        QuerySetRule.objects.create(
            drip=model_drip,
            field_name="date_joined",
            lookup_type="lt",
            field_value="now-{shift_one} days".format(shift_one=shift_one),
        )
        QuerySetRule.objects.create(
            drip=model_drip,
            field_name="date_joined",
            lookup_type="gte",
            field_value="now-{shift_two} days".format(shift_two=shift_two),
        )
        return model_drip

    def test_custom_drip(self):
        """
        Test a simple
        """
        model_drip = self.build_joined_date_drip()
        drip = model_drip.drip

        # ensure we are starting from a blank slate
        # 2 people meet the criteria
        self.assertEqual(2, drip.get_queryset().count())
        drip.prune()
        # no one is pruned, never sent before
        self.assertEqual(2, drip.get_queryset().count())
        # confirm nothing sent before
        self.assertEqual(0, SentDrip.objects.count())

        # send the drip
        drip.send()
        self.assertEqual(2, SentDrip.objects.count())  # got sent

        for sent in SentDrip.objects.all():
            self.assertIn("HELLO", sent.subject)
            self.assertIn("KETTEHS ROCK", sent.body)

        # subsequent runs reflect previous activity
        drip = Drip.objects.get(id=model_drip.id).drip
        # 2 people meet the criteria
        self.assertEqual(2, drip.get_queryset().count())
        drip.prune()
        self.assertEqual(0, drip.get_queryset().count())  # everyone is pruned

    def test_custom_short_term_drip(self):
        model_drip = self.build_joined_date_drip(shift_one=3, shift_two=4)
        drip = model_drip.drip

        # ensure we are starting from a blank slate
        # 2 people meet the criteria
        self.assertEqual(2, drip.get_queryset().count())

    def test_custom_date_range_walk(self):
        model_drip = self.build_joined_date_drip()
        drip = model_drip.drip

        # vanilla (now-8, now-7), past (now-8-3, now-7-3),
        # future (now-8+1, now-7+1)
        for count, shifted_drip in zip([0, 2, 2, 2, 2], drip.walk(into_past=3, into_future=2)):
            self.assertEqual(count, shifted_drip.get_queryset().count())

        # no reason to change after a send...
        drip.send()
        drip = Drip.objects.get(id=model_drip.id).drip

        # vanilla (now-8, now-7), past (now-8-3, now-7-3),
        # future (now-8+1, now-7+1)
        for count, shifted_drip in zip([0, 2, 2, 2, 2], drip.walk(into_past=3, into_future=2)):
            self.assertEqual(count, shifted_drip.get_queryset().count())

    def test_custom_drip_with_count(self):
        model_drip = self.build_joined_date_drip()
        QuerySetRule.objects.create(
            drip=model_drip,
            field_name="profile__credits",
            lookup_type="gte",
            field_value="5",
        )
        drip = model_drip.drip

        # 1 person meet the criteria
        self.assertEqual(1, drip.get_queryset().count())

        for count, shifted_drip in zip([0, 1, 1, 1, 1], drip.walk(into_past=3, into_future=2)):
            self.assertEqual(count, shifted_drip.get_queryset().count())

    def test_exclude_and_include(self):
        model_drip = Drip.objects.create(
            name="A Custom Week Ago",
            subject_template="HELLO {{ user.username }}",
            body_html_template="KETTEHS ROCK!",
        )
        QuerySetRule.objects.create(
            drip=model_drip,
            field_name="profile__credits",
            lookup_type="gte",
            field_value="1",
        )
        QuerySetRule.objects.create(
            drip=model_drip,
            field_name="profile__credits",
            method_type="exclude",
            lookup_type="exact",
            field_value=100,
        )
        QuerySetRule.objects.create(
            drip=model_drip,
            field_name="profile__credits",
            method_type="exclude",
            lookup_type="exact",
            field_value=125,
        )
        # 7 people meet the criteria
        self.assertEqual(7, model_drip.drip.get_queryset().count())

    def test_custom_drip_static_datetime(self):
        model_drip = self.build_joined_date_drip()
        QuerySetRule.objects.create(
            drip=model_drip,
            field_name="date_joined",
            lookup_type="lte",
            field_value=(timezone.now() - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S"),
        )
        drip = model_drip.drip

        for count, shifted_drip in zip([0, 2, 2, 0, 0], drip.walk(into_past=3, into_future=2)):
            self.assertEqual(count, shifted_drip.get_queryset().count())

    def test_custom_drip_static_now_datetime(self):
        model_drip = Drip.objects.create(
            name="A Custom Week Ago",
            subject_template="HELLO {{ user.username }}",
            body_html_template="KETTEHS ROCK!",
        )
        QuerySetRule.objects.create(
            drip=model_drip,
            field_name="date_joined",
            lookup_type="gte",
            field_value=(timezone.now() - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00"),
        )
        drip = model_drip.drip

        # catches "today and yesterday" users
        for count, shifted_drip in zip([4, 4, 4, 4, 4], drip.walk(into_past=3, into_future=3)):
            self.assertEqual(count, shifted_drip.get_queryset().count())

    def test_admin_timeline_prunes_user_output(self):
        """
        multiple users in timeline is confusing.
        """
        admin = self.User.objects.create(username="admin", email="admin@example.com")
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        # create a drip campaign that will surely give us duplicates.
        model_drip = Drip.objects.create(
            name="A Custom Week Ago",
            subject_template="HELLO {{ user.username }}",
            body_html_template="KETTEHS ROCK!",
        )
        QuerySetRule.objects.create(
            drip=model_drip,
            field_name="date_joined",
            lookup_type="gte",
            field_value=(timezone.now() - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00"),
        )

        # then get it's admin view.
        rf = RequestFactory()
        timeline_url = reverse(
            "admin:drip_timeline",
            kwargs={
                "drip_id": model_drip.id,
                "into_past": 3,
                "into_future": 3,
            },
        )

        request = rf.get(timeline_url)
        request.user = admin

        match = resolve(timeline_url)

        response = match.func(request, *match.args, **match.kwargs)

        # check that our admin (not excluded from test) is shown once.
        self.assertEqual(unicode(response.content).count(admin.email), 1)

    ##################
    #   TEST M2M     #
    ##################

    def test_annotated_field_name_property_no_count(self):
        model_drip = Drip.objects.create(
            name="A Custom Week Ago",
            subject_template="HELLO {{ user.username }}",
            body_html_template="KETTEHS ROCK!",
        )

        qsr = QuerySetRule.objects.create(
            drip=model_drip,
            field_name="date_joined",
            lookup_type="exact",
            field_value=2,
        )
        self.assertEqual(qsr.annotated_field_name, "date_joined")

    def test_annotated_field_name_property_with_count(self):

        model_drip = Drip.objects.create(
            name="A Custom Week Ago",
            subject_template="HELLO {{ user.username }}",
            body_html_template="KETTEHS ROCK!",
        )

        qsr = QuerySetRule.objects.create(
            drip=model_drip,
            field_name="userprofile__user__groups__count",
            lookup_type="exact",
            field_value=2,
        )

        self.assertEqual(
            qsr.annotated_field_name,
            "num_userprofile_user_groups",
        )

    def test_apply_annotations_no_count(self):

        model_drip = Drip.objects.create(
            name="A Custom Week Ago",
            subject_template="HELLO {{ user.username }}",
            body_html_template="KETTEHS ROCK!",
        )

        qsr: QuerySetRule = QuerySetRule.objects.create(
            drip=model_drip,
            field_name="date_joined",
            lookup_type="exact",
            field_value=(timezone.now()).strftime("%Y-%m-%d 00:00:00"),
        )
        base_queryset = model_drip.drip.get_queryset()
        qs = qsr.apply_any_annotation(base_queryset)

        self.assertEqual(qs, base_queryset)

    def test_apply_annotations_with_count(self):

        model_drip = Drip.objects.create(
            name="A Custom Week Ago",
            subject_template="HELLO {{ user.username }}",
            body_html_template="KETTEHS ROCK!",
        )

        qsr: QuerySetRule = QuerySetRule.objects.create(
            drip=model_drip,
            field_name="profile__user__groups__count",
            lookup_type="exact",
            field_value=2,
        )

        qs = qsr.apply_any_annotation(model_drip.drip.get_queryset())
        self.assertEqual(
            list(qs.query.annotation_select.keys()),  # type: ignore
            ["num_profile_user_groups"],
        )

    def test_apply_multiple_rules_with_aggregation(self):

        model_drip = Drip.objects.create(
            name="A Custom Week Ago",
            subject_template="HELLO {{ user.username }}",
            body_html_template="KETTEHS ROCK!",
        )

        qsr = QuerySetRule.objects.create(
            drip=model_drip,
            field_name="profile__user__groups__count",
            lookup_type="exact",
            field_value="0",
        )

        QuerySetRule.objects.create(
            drip=model_drip,
            field_name="date_joined",
            lookup_type="gte",
            field_value=(timezone.now() - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00"),
        )

        qsr.clean()
        qs = model_drip.drip.apply_queryset_rules(model_drip.drip.get_queryset())

        self.assertEqual(qs.count(), 4)

    def test_apply_and_or_queryset_ruletype(self):

        model_drip = Drip.objects.create(
            name="A Custom Week Ago",
            subject_template="HELLO {{ user.username }}",
            body_html_template="KETTEHS ROCK!",
        )

        qsr = QuerySetRule.objects.create(
            drip=model_drip,
            field_name="profile__user__groups__count",
            lookup_type="exact",
            field_value="0",
        )

        QuerySetRule.objects.create(
            drip=model_drip,
            field_name="date_joined",
            lookup_type="gte",
            field_value=(timezone.now() - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00"),
            rule_type="or",
        )

        qsr.clean()
        qs = model_drip.drip.apply_queryset_rules(model_drip.drip.get_queryset())

        self.assertEqual(qs.count(), 20)

    def test_apply_or_queryset_ruletype(self):

        model_drip = Drip.objects.create(
            name="A Custom Week Ago",
            subject_template="HELLO {{ user.username }}",
            body_html_template="KETTEHS ROCK!",
        )

        # returns 9 entries
        qsr = QuerySetRule.objects.create(
            drip=model_drip,
            field_name="profile__credits",
            lookup_type="gte",
            field_value="5",
            rule_type="or",
        )
        # returns 4 entries
        QuerySetRule.objects.create(
            drip=model_drip,
            field_name="date_joined",
            lookup_type="gte",
            field_value=(timezone.now() - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00"),
            rule_type="or",
        )
        qsr.clean()
        qs = model_drip.drip.apply_queryset_rules(model_drip.drip.get_queryset())

        self.assertEqual(qs.count(), 12)


class UrlsTestCase(TestCase):
    def test_drip_timeline_url(self):
        timeline_url = reverse(
            "admin:drip_timeline",
            kwargs={
                "drip_id": 1,
                "into_past": 2,
                "into_future": 3,
            },
        )

        self.assertEqual(timeline_url, "/admin/drip/drip/1/timeline/2/3/")

    def test_view_drip_email_url(self):
        view_drip_email_url = reverse(
            "admin:view_drip_email",
            kwargs={
                "drip_id": 1,
                "into_past": 2,
                "into_future": 3,
                "user_id": 4,
            },
        )

        self.assertEqual(
            view_drip_email_url,
            "/admin/drip/drip/1/timeline/2/3/4/",
        )

    @patch("drip.admin.get_user_model", new=get_user_model_mock)
    def test_drip_timeline_url_user_uuid(self):
        test_admin = DripAdmin(model=Drip, admin_site=AdminSite())
        new_urls = test_admin.get_urls()
        test_url_pattern = None
        for url_pattern in new_urls:
            if url_pattern.name == "view_drip_email":
                test_url_pattern = url_pattern
                break
        self.assertIsNotNone(test_url_pattern)
        self.assertEqual(
            test_url_pattern.pattern._route,  # type: ignore
            "<int:drip_id>/timeline/<int:into_past>/<int:into_future>/<uuid:user_id>/",  # noqa
        )
