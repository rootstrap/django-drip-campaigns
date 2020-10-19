from django.dispatch import Signal

"""
This signal is triggered upon sms message, you can define a receiver in your
project and handle sending the sms message
Args:
    drip: Drip campaign instance
        (to get the sms message content or any other needed attrs)
    user: An instance of whatever model you define to be a user for the drip
        using "DRIP_CAMPAIGN_USER_MODEL"
            (to get the user phone_number or any other needed attrs)
"""
post_drip = Signal(providing_args=['drip', 'user'])
