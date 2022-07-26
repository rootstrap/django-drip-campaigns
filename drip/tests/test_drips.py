from datetime import timedelta
from typing import Any, Dict, Optional
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.core.management import call_command
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import resolve, reverse
from django.utils import timezone

from credits.models import Profile
from drip.admin import DripAdmin
from drip.drips import DEFAULT_DRIP_MESSAGE_CLASS, DripBase, configured_message_classes
from drip.models import Drip, QuerySetRule, SentDrip
from drip.scheduler.cron_scheduler import cron_send_drips
from drip.utils import get_user_model, unicode

pytestmark = pytest.mark.django_db


def get_user_model_mock():
    from drip.models import TestUserUUIDModel

    return TestUserUUIDModel


User = get_user_model()

DEFAULT_MESSAGE_CLASSES_LENGTH = len(configured_message_classes().items())


class SetupDataDripMixin:
    NUM_STRING = [
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

    def build_user_data(self):
        """
        Creates 20 users, half of which buy 25 credits a day,
        and the other half that does none.
        """
        start = timezone.now() - timedelta(hours=2)
        for i, name in enumerate(self.NUM_STRING):
            user = User.objects.create(
                username="{name}_25_credits_a_day".format(name=name),
                email="{name}@test.com".format(name=name),
            )
            User.objects.filter(id=user.id).update(
                date_joined=start - timedelta(days=i),
            )

            profile = Profile.objects.get(user=user)
            profile.credits = i * 25
            profile.save()

        for i, name in enumerate(self.NUM_STRING):
            user = User.objects.create(
                username="{name}_no_credits".format(name=name),
                email="{name}@test.com".format(name=name),
            )
            User.objects.filter(id=user.id).update(
                date_joined=start - timedelta(days=i),
            )

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


class TestCaseDrips(SetupDataDripMixin):
    def setup_method(self, test_method):
        self.build_user_data()

    def test_users_exists(self):
        assert 20 == User.objects.all().count()

    @pytest.mark.parametrize(
        "start_days, end_days, filter_dict, count_users",
        (
            (1, 0, {}, 2),  # test_day_zero_users
            (3, 2, {"profile__credits__gt": 0}, 1),  # test_day_two_users_active
            (3, 2, {"profile__credits": 0}, 1),  # test_day_two_users_inactive
            (8, 7, {"profile__credits__gt": 0}, 1),  # test_day_seven_users_active
            (8, 7, {"profile__credits": 0}, 1),  # test_day_seven_users_inactive
            (15, 14, {"profile__credits__gt": 0}, 0),  # test_day_fourteen_users_active
            (15, 14, {"profile__credits": 0}, 0),  # test_day_fourteen_users_inactive
        ),
    )
    def test_multiple_days_users_filter(
        self, start_days: int, end_days: int, filter_dict: Dict[str, Any], count_users: int
    ):
        start = timezone.now() - timedelta(days=start_days)
        end = timezone.now() - timedelta(days=end_days)
        assert (
            count_users
            == User.objects.filter(
                date_joined__range=(start, end),
                **filter_dict,
            ).count()
        )

    ########################
    #   RELATION SNAGGER   #
    ########################

    def test_get_simple_fields(self):
        from drip.utils import get_simple_fields

        simple_fields = get_simple_fields(User)
        assert bool([sf for sf in simple_fields if "profile" in sf[0]])

    ##################
    #   TEST DRIPS   #
    ##################

    def test_backwards_drip_class(self):
        for drip in Drip.objects.all():
            assert issubclass(drip.drip.__class__, DripBase)

    def test_custom_drip(self):
        """
        Test a simple
        """
        model_drip = self.build_joined_date_drip()
        drip = model_drip.drip

        # ensure we are starting from a blank slate
        # 2 people meet the criteria
        assert 2 == drip.get_queryset().count()
        drip.prune()
        # no one is pruned, never sent before
        assert 2 == drip.get_queryset().count()
        # confirm nothing sent before
        assert 0 == SentDrip.objects.count()

        # send the drip
        drip.send()
        assert 2 == SentDrip.objects.count()  # got sent

        for sent in SentDrip.objects.all():
            assert "HELLO" in sent.subject
            assert "KETTEHS ROCK" in sent.body

        # subsequent runs reflect previous activity
        drip = Drip.objects.get(id=model_drip.id).drip
        # 2 people meet the criteria
        assert 2 == drip.get_queryset().count()
        drip.prune()
        assert 0 == drip.get_queryset().count()  # everyone is pruned

    def test_custom_short_term_drip(self):
        model_drip = self.build_joined_date_drip(shift_one=3, shift_two=4)
        drip = model_drip.drip

        # ensure we are starting from a blank slate
        # 2 people meet the criteria
        assert 2 == drip.get_queryset().count()

    def test_custom_date_range_walk(self):
        model_drip = self.build_joined_date_drip()
        drip = model_drip.drip

        # vanilla (now-8, now-7), past (now-8-3, now-7-3),
        # future (now-8+1, now-7+1)
        for count, shifted_drip in zip([0, 2, 2, 2, 2], drip.walk(into_past=3, into_future=2)):
            assert count == shifted_drip.get_queryset().count()

        # no reason to change after a send...
        drip.send()
        drip = Drip.objects.get(id=model_drip.id).drip

        # vanilla (now-8, now-7), past (now-8-3, now-7-3),
        # future (now-8+1, now-7+1)
        for count, shifted_drip in zip([0, 2, 2, 2, 2], drip.walk(into_past=3, into_future=2)):
            assert count == shifted_drip.get_queryset().count()

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
        assert 1 == drip.get_queryset().count()

        for count, shifted_drip in zip([0, 1, 1, 1, 1], drip.walk(into_past=3, into_future=2)):
            assert count == shifted_drip.get_queryset().count()

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
        assert 7 == model_drip.drip.get_queryset().count()

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
            assert count == shifted_drip.get_queryset().count()

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
            assert count == shifted_drip.get_queryset().count()

    def test_admin_timeline_prunes_user_output(self):
        """
        multiple users in timeline is confusing.
        """
        admin = User.objects.create(username="admin", email="admin@example.com")
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
        assert 1 == unicode(response.content).count(admin.email)

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
        assert qsr.annotated_field_name == "date_joined"

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
        assert qsr.annotated_field_name == "num_userprofile_user_groups"

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

        assert qs == base_queryset

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
        assert list(qs.query.annotation_select.keys()) == ["num_profile_user_groups"]  # type: ignore

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
        assert qs.count() == 4

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

        assert qs.count() == 20

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

        assert qs.count() == 12

    @pytest.mark.parametrize(
        "message_class_config, lenght_plus, default_class, custom_class",
        (
            (
                {"non-default-class": "drip.drips.OtherDripClass"},
                1,
                DEFAULT_DRIP_MESSAGE_CLASS,
                None,
            ),  # adding a brand new MessageClass
            (
                {"default": "drip.drips.OtherDripClass"},
                0,
                "drip.drips.OtherDripClass",
                None,
            ),  # Replacing an existing Message Class
            (
                {
                    "default": "drip.drips.OtherDripClass",
                    "custom": "custom.module.ClassName",
                },
                1,
                "drip.drips.OtherDripClass",
                "custom.module.ClassName",
            ),  # Mixing replacing and adding a new class
        ),
    )
    def test_message_class_for(
        self,
        message_class_config: Dict[str, str],
        lenght_plus: int,
        default_class: str,
        custom_class: Optional[str],
    ):
        setattr(
            settings,
            "DRIP_MESSAGE_CLASSES",
            message_class_config,
        )

        message_classes = configured_message_classes()

        assert len(message_classes.items()) == DEFAULT_MESSAGE_CLASSES_LENGTH + lenght_plus
        assert message_classes["default"] == default_class
        if custom_class:
            assert message_classes["custom"] == custom_class


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

        assert timeline_url == "/admin/drip/drip/1/timeline/2/3/"

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

        assert view_drip_email_url == "/admin/drip/drip/1/timeline/2/3/4/"

    @patch("drip.admin.get_user_model", new=get_user_model_mock)
    def test_drip_timeline_url_user_uuid(self):
        test_admin = DripAdmin(model=Drip, admin_site=AdminSite())
        new_urls = test_admin.get_urls()
        test_url_pattern = None
        for url_pattern in new_urls:
            if url_pattern.name == "view_drip_email":
                test_url_pattern = url_pattern
                break
        assert test_url_pattern is not None
        assert (
            test_url_pattern.pattern._route  # type: ignore
            == "<int:drip_id>/timeline/<int:into_past>/<int:into_future>/<uuid:user_id>/"
        )


@pytest.fixture(scope="session")
def celery_includes():
    return [
        "drip.tasks",
    ]


class TestScheduler:
    def test_celery_beat_schedule(self, celery_app, celery_worker):
        task_name = "drip.tasks.call_send_drips_celery_command()"
        assert task_name in celery_app.conf.beat_schedule

    def test_cron_jobs_schedule(self):
        # CELERY default config
        cron_scheduler = cron_send_drips()
        assert cron_scheduler is None

        # CRON config
        setattr(
            settings,
            "DRIP_SCHEDULE_SETTINGS",
            {
                "DRIP_SCHEDULE": True,
                "DRIP_SCHEDULE_DAY_OF_WEEK": "*",
                "DRIP_SCHEDULE_HOUR": 12,
                "DRIP_SCHEDULE_MINUTE": 00,
                "SCHEDULER": "CRON",
            },
        )
        cron_scheduler = cron_send_drips()
        assert cron_scheduler
        jobs = cron_scheduler.get_jobs()
        expected_job_name = "cron_send_drips.<locals>.call_send_drips_command"
        assert expected_job_name in [job.name for job in jobs]


class TestSendDripsCommand(SetupDataDripMixin):
    @pytest.mark.parametrize(
        "build_users, model_drip_enabled, sent_drip_count, drip_count_queryset",
        (
            (True, True, 2, 2),  # Sucess case, the command send drips to users.
            (False, True, 0, 0),  # No users at all, enabled drip.
            (True, False, 0, 2),  # Disabled drip, the command will not get this drip
            (False, False, 0, 0),  # No users at all, disabled drip.
        ),
    )
    def test_send_drips_command(
        self, build_users: bool, model_drip_enabled: bool, sent_drip_count: int, drip_count_queryset: int
    ):
        if build_users:
            self.build_user_data()
        model_drip = self.build_joined_date_drip()
        model_drip.enabled = model_drip_enabled
        model_drip.save()

        call_command("send_drips")

        assert sent_drip_count == SentDrip.objects.count()
        model_drip.refresh_from_db()
        drip = model_drip.drip
        assert drip_count_queryset == drip.get_queryset().count()
