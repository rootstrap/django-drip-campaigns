from celery import current_app
from celery.schedules import crontab
from django.conf import settings
from django.core.management import call_command

app = current_app._get_current_object()


DRIP_SCHEDULE_SETTINGS = getattr(settings, "DRIP_SCHEDULE_SETTINGS", {})

DRIP_SCHEDULE = DRIP_SCHEDULE_SETTINGS.get("DRIP_SCHEDULE", False)
DRIP_SCHEDULE_DAY_OF_WEEK = DRIP_SCHEDULE_SETTINGS.get("DRIP_SCHEDULE_DAY_OF_WEEK", 0)
DRIP_SCHEDULE_HOUR = DRIP_SCHEDULE_SETTINGS.get("DRIP_SCHEDULE_HOUR", 0)
DRIP_SCHEDULE_MINUTE = DRIP_SCHEDULE_SETTINGS.get("DRIP_SCHEDULE_MINUTE", 0)
CELERY_ENABLED = DRIP_SCHEDULE_SETTINGS.get("CELERY_ENABLED", False)

if DRIP_SCHEDULE and CELERY_ENABLED:

    @app.task
    def call_send_drips_celery_command():
        call_command("send_drips")


@app.on_after_finalize.connect
def app_ready_drip(sender, **kwargs):
    if DRIP_SCHEDULE and CELERY_ENABLED:
        sender.add_periodic_task(
            crontab(
                day_of_week=DRIP_SCHEDULE_DAY_OF_WEEK,
                hour=DRIP_SCHEDULE_HOUR,
                minute=DRIP_SCHEDULE_MINUTE,
            ),
            call_send_drips_celery_command,
        )
