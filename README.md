[![Maintainability](https://api.codeclimate.com/v1/badges/5240f5a755d873846f8f/maintainability)](https://codeclimate.com/repos/5f0c9d52db4bad011400189e/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/5240f5a755d873846f8f/test_coverage)](https://codeclimate.com/repos/5f0c9d52db4bad011400189e/test_coverage)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Django Drip Campaigns

![Build Status](https://github.com/rootstrap/django-drip-campaigns/actions/workflows/drip-django.yaml/badge.svg?branch=master)

Drip campaigns are pre-written sets of emails sent to customers or prospects over time. Django Drips lets you use the admin to manage drip campaign emails using querysets on Django's User model.

This project is a fork of the one written by [Zapier](https://zapier.com/z/qO/).

#### You can check out the docs [here](https://django-drip-campaigns.readthedocs.io/en/latest/).

## Installation:

1. Install django-drip-campaings using pip:

```
pip install django-drip-campaigns
```

2. Add `'drip'` to your `INSTALLED_APPS` list on your settings.

```python
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.comments',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',

    # ...

    'drip',
]
```

3. (Optional) Set `DRIP_FROM_EMAIL = '<your_app_from_email>'` in your settings, where `<your_app_from_email>` is the email account that is going to be shown in the sent emails. Otherwise `EMAIL_HOST_USER` value will be used.

4. Finally, run `python manage.py migrate drip` to set up the necessary database tables.

## Usage

If you haven't, create a superuser with the [Django createsuperuser command](https://docs.djangoproject.com/en/3.0/intro/tutorial02/#creating-an-admin-user). Login with the admin user, and select `Drips` to manage them. You will be able to:

- View created drips.
- Create a new drip.
- Select and delete drips.

Now you can also manage campaigns, select ``Campaigns`` to manage them. You will be able to:
- View created campaigns.
- Create a new campaign.
- Select and delete campaign.

### Create Campaign

In the Django admin, after select `Campaigns`, you can click on `ADD CAMPAIGN +` button to create a new one. You will see the `add campaign` page:

![Add Campaign](https://raw.githubusercontent.com/rootstrap/django-drip-campaigns/master/docs/images/campaign_creation.png)

When you create a campaign, you need to decide if the related drips will be deleted along with the campaign, using the `Delete drips` field.

Here you will find an inline creation or edition for `Drips` this will not include the `QUERY SET RULES` section. It will only allow you to change the mail content in the Drip.

Campaigns will allow you to manage many Drips that need to be related between them.

### Create Drip

In the Django admin, after select `Drips`, you can click on `ADD DRIP +` button to create a new one. You will see the `add drip` page:

![Add Drip](https://raw.githubusercontent.com/rootstrap/django-drip-campaigns/master/docs/images/add_drip_page.png)

Here you can relate the Drip to the corresponding ``Campaign``. Grouping several drips under a campaign.

On the `FIELD NAME OF USER` input, when you click on it, you will be able to view:

- The fields of your user's model.
- The fields of your user's model in other models that are related with it.

Please take a look a this example:

![Lookup fields](https://raw.githubusercontent.com/rootstrap/django-drip-campaigns/master/docs/images/users_lookup_fields.png)

With this, you can select one or more fields to create useful drips.
Additionally if you select a field name of user that has a date type, you can enter in the `FIELD VALUE` input, a date value written in natural language that combines operations on the current datetime.
For example, if you have selected the field `last_login` that has a date type, and you want to create a drip to send emails to the users who logged in exactly one week ago; you can enter:

```
now-1 week
```

or

```
now- 1 w
```

Possible operations and values:

- Add (`+`) or subtract (`-`) dates.
- On the left side of the operation, write the current datetime value: `now`.
- On the right side of the operation:
  - `seconds` or `s`.
  - `minutes` or `m`.
  - `hours` or `h`.
  - `days` or `d`.
  - `weeks` or `w`.
  - If you enter the number `1`, you can write `second`, `minute`, etc.
  - Don't enter a space between `now` and the operation symbol. Optionally you can add (or not) a space around the number value.

Let's see some examples of the date values that you can enter:

- `now-1 day`
- `now+ 8days`
- `now+ 1 h`
- `now-4hours`
- `now- 3 weeks`
- `now-1 weeks`

### View Timeline

In the Django admin, you can select a drip and then click on the `VIEW TIMELINE` button to view the mails expected to be sent with the corresponding receivers:

![Timeline](https://raw.githubusercontent.com/rootstrap/django-drip-campaigns/master/docs/images/view_timeline.png)

### Send drips

To send the created and enabled drips, run the command:

```
python manage.py send_drips
```

You can use cron to schedule the drips.

### The cron scheduler

You may want to have an easy way to send drips periodically. It's possible to set a couple of parameters in your settings to do that. First activate the scheduler by adding the `DRIP_SCHEDULE_SETTINGS` dictionary:

```python
# your settings file
DRIP_SCHEDULE_SETTINGS = {
   'DRIP_SCHEDULE': True,
}

```

After that, choose:

- A day of the week: An integer value between `0-6`, or a string: `'mon'`, `'tue'`, `'wed'`, `'thu'`, `'fri'`, `'sat'`, `'sun'`. The name in the settings is `DRIP_SCHEDULE_DAY_OF_WEEK` (default is set to `0`).
- An hour: An integer value between `0-23`. The name in the settings is `DRIP_SCHEDULE_HOUR` (default is set to `0`).
- A minute: An integer value between `0-59`. The name in the settings is `DRIP_SCHEDULE_MINUTE` (default is set to `0`).

With those values, a cron scheduler will execute the `send_drips` command every week in the specified day/hour/minute. The scheduler will use the timezone of your `TIME_ZONE` parameter in your settings (default is set to `'UTC'`). For example, if you have:

```python
DRIP_SCHEDULE_SETTINGS = {
   'DRIP_SCHEDULE': True,
   'DRIP_SCHEDULE_DAY_OF_WEEK': 'mon',
   'DRIP_SCHEDULE_HOUR': 13,
   'DRIP_SCHEDULE_MINUTE': 57,
}
```

Then every Monday at 13:57 the `send_drips` command will be executed.
Last but not least, add this line at the end of your main `urls.py` file to start the scheduler:

```python
# your main urls.py file
...
from drip.scheduler.cron_scheduler import cron_send_drips

...
cron_send_drips()
```

We recommend you to do it there because we know for sure that it's a file that is executed once at the beginning.

Some tips:

- If you want to run the command every day in the week, hour, or minute, just set the corresponding parameter to `'*'`.
- If you want to run the command more than a day in the week, just set the `DRIP_SCHEDULE_DAY_OF_WEEK` to more than one value. For example, if you set that to `'mon-fri'` the command will be executed from Monday to Friday.


### Celery integration
IMPORTANT: We use Celery 5.2.2 that supports Django 1.11 LTS or newer versions.

If you need to use celery it can be configured in the same way you just need to add the following key `SCHEDULER` setted as `"CELERY"`:
```python
DRIP_SCHEDULE_SETTINGS = {
   'DRIP_SCHEDULE': True,
   'DRIP_SCHEDULE_DAY_OF_WEEK': 'mon',
   'DRIP_SCHEDULE_HOUR': 13,
   'DRIP_SCHEDULE_MINUTE': 57,
   'SCHEDULER': "CELERY",
}
```
The default value of this key is `"CRON"`, if you enable `DRIP_SCHEDULE` it will work with a Cron by default.

In order to make this happen, the project's `celery.py` setup shall invoke the
[autodiscoverttasks](https://docs.celeryproject.org/en/latest/reference/celery.html#celery.Celery.autodiscover_tasks)
function. This task is scheduled with a simple
[Celery beat configuration](https://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#entries).
