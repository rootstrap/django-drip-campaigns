from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.core.management import call_command

from drip.scheduler.constants import SCHEDULER_CRON, get_drip_scheduler_settings


def cron_send_drips():
    def call_send_drips_command():
        call_command("send_drips")

    (
        DRIP_SCHEDULE,
        DRIP_SCHEDULE_DAY_OF_WEEK,
        DRIP_SCHEDULE_HOUR,
        DRIP_SCHEDULE_MINUTE,
        SCHEDULER,
    ) = get_drip_scheduler_settings()
    CRON_ENABLED = SCHEDULER == SCHEDULER_CRON
    if DRIP_SCHEDULE and CRON_ENABLED:
        cron_scheduler = BackgroundScheduler()
        cron_scheduler.add_job(
            call_send_drips_command,
            "cron",
            day_of_week=DRIP_SCHEDULE_DAY_OF_WEEK,
            hour=DRIP_SCHEDULE_HOUR,
            minute=DRIP_SCHEDULE_MINUTE,
            timezone=getattr(settings, "TIME_ZONE", "UTC"),
        )
        cron_scheduler.start()
        return cron_scheduler
