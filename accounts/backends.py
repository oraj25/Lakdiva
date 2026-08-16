from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrStaffBackend(ModelBackend):
    """
    Allow Lakdiva SecurePOS users to log in using either:

    - Email address
    - Staff number

    Example:
        admin@lakdiva.lk
        ADM001
    """

    def authenticate(
        self,
        request,
        username=None,
        password=None,
        **kwargs,
    ):
        UserModel = get_user_model()

        if username is None:
            username = kwargs.get("email")

        if not username or password is None:
            return None

        identifier = username.strip()

        user = None

        # -------------------------------------------------
        # Try email first
        # -------------------------------------------------

        try:
            user = UserModel.objects.get(
                email__iexact=identifier
            )

        except UserModel.DoesNotExist:

            # ---------------------------------------------
            # If email was not found, try staff number
            # ---------------------------------------------

            try:
                user = UserModel.objects.get(
                    staff_no__iexact=identifier
                )

            except UserModel.DoesNotExist:

                # Perform a password hash operation even
                # when the user does not exist.
                #
                # This reduces timing differences between
                # valid and invalid account identifiers.

                UserModel().set_password(password)

                return None

        # -------------------------------------------------
        # Check password + account status
        # -------------------------------------------------

        if (
            user.check_password(password)
            and self.user_can_authenticate(user)
        ):
            return user

        return None