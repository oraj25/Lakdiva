from django.contrib.auth.base_user import (
    AbstractBaseUser,
    BaseUserManager,
)
from django.contrib.auth.models import PermissionsMixin
from django.db import models

import accounts


# =========================================================
# ROLE MODEL
# =========================================================

class Role(models.Model):

    EMPLOYEE = "EMPLOYEE"
    ADMIN = "ADMIN"

    ROLE_CHOICES = [
        (EMPLOYEE, "Employee"),
        (ADMIN, "Administrator"),
    ]

    role_id = models.BigAutoField(
        primary_key=True
    )

    role_name = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        unique=True,
    )

    class Meta:
        db_table = "roles"
        ordering = ["role_name"]

    def __str__(self):
        return self.get_role_name_display()


# =========================================================
# USER MANAGER
# =========================================================

class UserManager(BaseUserManager):

    use_in_migrations = True

    def create_user(
        self,
        email,
        staff_no,
        full_name,
        password=None,
        role=None,
        **extra_fields,
    ):

        if not email:
            raise ValueError(
                "Users must have an email address."
            )

        if not staff_no:
            raise ValueError(
                "Users must have a staff number."
            )

        if not full_name:
            raise ValueError(
                "Users must have a full name."
            )

        email = self.normalize_email(email)

        # Normal users default to EMPLOYEE role
        if role is None:
            role, _ = Role.objects.get_or_create(
                role_name=Role.EMPLOYEE
            )

        user = self.model(
            email=email,
            staff_no=staff_no,
            full_name=full_name,
            role=role,
            **extra_fields,
        )

        # IMPORTANT:
        # Never store plaintext passwords.
        user.set_password(password)

        user.save(
            using=self._db
        )

        return user

    def create_superuser(
        self,
        email,
        staff_no,
        full_name,
        password=None,
        **extra_fields,
    ):

        extra_fields.setdefault(
            "is_staff",
            True,
        )

        extra_fields.setdefault(
            "is_superuser",
            True,
        )

        extra_fields.setdefault(
            "status",
            "Active",
        )

        if extra_fields.get("is_staff") is not True:
            raise ValueError(
                "Superuser must have is_staff=True."
            )

        if extra_fields.get(
            "is_superuser"
        ) is not True:
            raise ValueError(
                "Superuser must have "
                "is_superuser=True."
            )

        admin_role, _ = Role.objects.get_or_create(
            role_name=Role.ADMIN
        )

        return self.create_user(
            email=email,
            staff_no=staff_no,
            full_name=full_name,
            password=password,
            role=admin_role,
            **extra_fields,
        )


# =========================================================
# CUSTOM USER MODEL
# =========================================================

class User(
    AbstractBaseUser,
    PermissionsMixin,
):

    class Status(models.TextChoices):
        ACTIVE = "Active", "Active"
        DISABLED = "Disabled", "Disabled"

    user_id = models.BigAutoField(
        primary_key=True
    )

    staff_no = models.CharField(
        max_length=30,
        unique=True,
    )

    full_name = models.CharField(
        max_length=150,
    )

    email = models.EmailField(
        unique=True,
    )

    # Django uses the Python field name "password".
    # The physical MySQL column will be "password_hash".
    password = models.CharField(
        max_length=128,
        db_column="password_hash",
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="users",
        db_column="role_id",
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    # Used by Django's admin interface.
    is_staff = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    objects = UserManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = [
        "staff_no",
        "full_name",
    ]

    EMAIL_FIELD = "email"

    class Meta:
        db_table = "users"
        ordering = ["full_name"]

    @property
    def is_active(self):
        """
        Django authentication checks this property.

        Disabled users are prevented from authenticating.
        """
        return self.status == self.Status.ACTIVE

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name.split()[0]

    def __str__(self):
        return (
            f"{self.staff_no} - "
            f"{self.full_name}"
        )

# =========================================================
# LOGIN ATTEMPT MODEL
# =========================================================

class LoginAttempt(models.Model):

    attempt_id = models.BigAutoField(
        primary_key=True
    )

    login_identifier = models.CharField(
        max_length=254,
        db_index=True,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_attempts",
    )

    success = models.BooleanField(
        default=False,
        db_index=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    attempted_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        db_table = "login_attempts"
        ordering = ["-attempted_at"]

    def __str__(self):
        status = (
            "SUCCESS"
            if self.success
            else "FAILED"
        )

        return (
            f"{self.login_identifier} - "
            f"{status}"
        )