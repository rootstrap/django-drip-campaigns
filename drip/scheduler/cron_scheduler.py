from django.conf import settings
from apscheduler.schedulers.background import BackgroundScheduler

from django.core.management import call_command


DRIP_SCHEDULE = getattr(
    settings, 'DRIP_SCHEDULE', False
)
DRIP_SCHEDULE_DAY_OF_WEEK = getattr(
    settings, 'DRIP_SCHEDULE_DAY_OF_WEEK', 0
)
DRIP_SCHEDULE_HOUR = getattr(
    settings, 'DRIP_SCHEDULE_HOUR', 0
)
DRIP_SCHEDULE_MINUTE = getattr(
    settings, 'DRIP_SCHEDULE_MINUTE', 0
)
DRIP_SCHEDULE_TZ = getattr(
    settings, 'TIME_ZONE', 'UTC'
)


def cron_send_drips():
    def call_send_drips_command():
        call_command('send_drips')

    if DRIP_SCHEDULE:
        cron_scheduler = BackgroundScheduler()
        cron_scheduler.add_job(
            call_send_drips_command,
            'cron',
            day_of_week=DRIP_SCHEDULE_DAY_OF_WEEK,
            hour=DRIP_SCHEDULE_HOUR,
            minute=DRIP_SCHEDULE_MINUTE,
            timezone=DRIP_SCHEDULE_TZ,
        )
        cron_scheduler.start()
