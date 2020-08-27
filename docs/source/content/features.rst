Features
=============

If you haven't, create a superuser with the `Django createsuperuser command <https://docs.djangoproject.com/en/3.0/intro/tutorial02/#creating-an-admin-user>`_. Login with the admin user, and select ``Drips`` to manage them. You will be able to:

- View created drips.
- Create a new drip.
- Select and delete drips.

Create Drip
-----------
Click on the ``ADD DRIP +`` button to create a new Drip. In the creation you need to define the email that you want to send, and the queryset for the users that will receive it. To see more details, :ref:`click here <create-drip>`.

View timeline of a Drip
-----------------------

In the django admin, you can select a drip and then click on the ``VIEW TIMELINE`` button to view the emails expected to be sent with the corresponding receivers:

.. image:: ../../images/view_timeline.png
  :width: 400
  :alt: View timeline

Message class
-------------

By default, Django Drip creates and sends messages that are instances of Django’s ``EmailMultiAlternatives`` class.
If you want to customize in any way the message that is created and sent, you can do that by creating a subclass of ``EmailMessage`` and overriding any method that you want to behave differently.
For example:

.. code-block:: python

    from django.core.mail import EmailMessage
    from drip.drips import DripMessage

    class PlainDripEmail(DripMessage):

        @property
        def message(self):
            if not self._message:
                email = EmailMessage(self.subject, self.plain, self.from_email, [self.user.email])
                self._message = email
            return self._message

In that example, ``PlainDripEmail`` overrides the message property of the base ``DripMessage`` class to create a simple
``EmailMessage`` instance instead of an ``EmailMultiAlternatives`` instance.

In order to be able to specify that your custom message class should be used for a drip, you need to configure it in the ``DRIP_MESSAGE_CLASSES`` setting:

.. code-block:: python

    DRIP_MESSAGE_CLASSES = {
        'plain': 'myproj.email.PlainDripEmail',
    }

This will allow you to choose in the admin, for each drip, whether the ``default`` (``DripMessage``) or ``plain`` message class should be used for generating and sending the messages to users.

Send Drips
----------

To send the created and enabled Drips, run the command:

.. code-block:: python

    python manage.py send_drips

You can use cron to schedule the drips.
