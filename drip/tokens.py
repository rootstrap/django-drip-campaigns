from typing import Optional, Tuple

from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_bytes, force_str
from django.utils.http import base36_to_int, urlsafe_base64_decode, urlsafe_base64_encode

from drip.models import Campaign, Drip
from drip.utils import get_user_model

User = get_user_model()


class CustomTokenGenerator(PasswordResetTokenGenerator):
    """
    Custom token generator with no login and password hashing.
    Also not checking time validation, it is just a hash of user data for email purposes.
    """

    def _make_hash_value(self, user: AbstractBaseUser, timestamp: int) -> str:
        """
        Build hash value ignoring login_timestamp and password for keeping it valid over time
        """
        email_field = user.get_email_field_name()
        email = getattr(user, email_field, "") or ""
        return f"{user.pk}{timestamp}{email}"

    def check_token(self, user: Optional[AbstractBaseUser], token: Optional[str]) -> bool:
        """
        Check that a password reset token is correct for a given user.
        Remove the check of token time validation
        """
        if not (user and token):
            return False
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(user, ts), token):
            # Ignore line because Mypy doesn't recognice the argument legacy
            if not constant_time_compare(
                self._make_token_with_timestamp(user, ts, legacy=True),  # type: ignore
                token,
            ):
                return False

        return True


custom_token_generator = CustomTokenGenerator()


class EmailToken:
    """
    A base object for managing token validations and generations for Drip id and user data.
    """

    user: AbstractBaseUser

    def __init__(self, user: AbstractBaseUser):
        self.user = user

    def _get_token(self) -> str:
        """
        Generate token using custom token generator class for user
        """
        return custom_token_generator.make_token(self.user)

    def _get_uidb64(self, data_id: int) -> str:
        """
        Generate uidb64 string for ids with url encode
        """
        # Mypy is not getting the result of force_bytes as bytes
        return urlsafe_base64_encode(force_bytes(data_id))  # type: ignore

    def get_uidb64_token(self, object_id: int) -> Tuple[str, str, str]:
        """
        Returns drip/campaign and user uidb64 and token for the user, for building url
        """
        drip_uidb64 = self._get_uidb64(object_id)
        uidb64, token = self.get_uidb64_token_user_only()
        return drip_uidb64, uidb64, token

    def get_uidb64_token_user_only(self) -> Tuple[str, str]:
        """
        Returns user uidb64 and token for the user, for building url
        """
        uidb64 = self._get_uidb64(self.user.pk)
        token = self._get_token()
        return uidb64, token

    @classmethod
    def validate_user_uidb64_token(cls, uidb64: str, token: str) -> Optional[AbstractBaseUser]:
        """
        Validates user uidb64 and token using custom token generator class
        and returns the User object for this variables
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if not custom_token_generator.check_token(user, token):
            return None
        return user

    @classmethod
    def validate_drip_uidb64(cls, drip_uidb64: str) -> Optional[Drip]:
        """
        Validates drip uidb64 and returns the Drip object for this string
        """
        try:
            drip_uid = force_str(urlsafe_base64_decode(drip_uidb64))
            drip = Drip.objects.get(pk=drip_uid)
        except (TypeError, ValueError, OverflowError, Drip.DoesNotExist):
            drip = None
        return drip

    @classmethod
    def validate_campaign_uidb64(cls, campaign_uidb64: str) -> Optional[Campaign]:
        """
        Validates campaign uidb64 and returns the Campaign object for this string
        """
        try:
            campaign_uid = force_str(urlsafe_base64_decode(campaign_uidb64))
            campaign = Campaign.objects.get(pk=campaign_uid)
        except (TypeError, ValueError, OverflowError, Campaign.DoesNotExist):
            campaign = None
        return campaign
