Installation and configuration
==============================
1. Install package from pypi:

.. code-block:: python

    pip install django-drip-campaigns

2. Add ``drip`` app to the ``INSTALLED_APPS`` list in your project settings:

.. code-block:: python

    INSTALLED_APPS = [
        ...,
        'django.contrib.contenttypes',
        'django.contrib.comments',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.admin',
        # ...
        'drip',
    ]


3. (Optional) Set ``DRIP_FROM_EMAIL = '<your_app_from_email>'`` in your settings, where ``<your_app_from_email>`` is the email account that is going to be shown in the sent emails. Otherwise ``EMAIL_HOST_USER`` value will be used.  

4. Finally, run ``migrate`` to set up the necessary database tables:

.. code-block:: python

    python manage.py migrate drip
