from celery import current_app
from celery.schedules import crontab
from django.core.management import call_command

from drip.scheduler.constants import SCHEDULER_CELERY, get_drip_scheduler_settings

(
    DRIP_SCHEDULE,
    DRIP_SCHEDULE_DAY_OF_WEEK,
    DRIP_SCHEDULE_HOUR,
    DRIP_SCHEDULE_MINUTE,
    SCHEDULER,
) = get_drip_scheduler_settings()

app = current_app._get_current_object()

CELERY_ENABLED = SCHEDULER == SCHEDULER_CELERY

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
