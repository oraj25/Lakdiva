from decimal import Decimal

from django.conf import settings

from django.core.validators import (
    MinValueValidator,
)

from django.db import models

from django.utils import timezone


# =========================================================
# POS TERMINAL
# =========================================================

class POSTerminal(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "Active", "Active"
        INACTIVE = "Inactive", "Inactive"

    pos_id = models.BigAutoField(
        primary_key=True
    )

    terminal_code = models.CharField(
        max_length=30,
        unique=True,
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "pos_terminals"
        ordering = ["terminal_code"]

    def __str__(self):
        return self.terminal_code


# =========================================================
# POS SHIFT
# =========================================================

class POSShift(models.Model):

    class Status(models.TextChoices):
        OPEN = "Open", "Open"
        COMPLETED = "Completed", "Completed"

    shift_id = models.BigAutoField(
        primary_key=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pos_shifts",
        db_column="user_id",
    )

    pos = models.ForeignKey(
        POSTerminal,
        on_delete=models.PROTECT,
        related_name="shifts",
        db_column="pos_id",
    )

    shift_start = models.DateTimeField(
        default=timezone.now
    )

    shift_end = models.DateTimeField(
        null=True,
        blank=True,
    )

    opening_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    cash_in = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    cash_out = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    closing_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    cash_variance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    handed_over_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_pos_handovers",
        db_column="handed_over_to",
    )

    handover_time = models.DateTimeField(
        null=True,
        blank=True,
    )

    handover_notes = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        db_table = "pos_shifts"

        ordering = [
            "-shift_start"
        ]

        indexes = [
            models.Index(
                fields=["user"]
            ),
            models.Index(
                fields=["pos"]
            ),
            models.Index(
                fields=["status"]
            ),
        ]

    @property
    def expected_cash(self):

        return (
            self.opening_cash
            + self.cash_in
            - self.cash_out
        )

    def calculate_variance(self):

        if self.closing_cash is None:
            return None

        return (
            self.closing_cash
            - self.expected_cash
        )

    def __str__(self):

        return (
            f"Shift {self.shift_id} - "
            f"{self.pos.terminal_code} - "
            f"{self.user.staff_no}"
        )


# =========================================================
# DAILY SECURITY CHECK
# =========================================================

class DailySecurityCheck(models.Model):

    class Result(models.TextChoices):
        NORMAL = "Normal", "Normal"
        SUSPICIOUS = "Suspicious", "Suspicious"

    check_id = models.BigAutoField(
        primary_key=True
    )

    shift = models.OneToOneField(
        POSShift,
        on_delete=models.CASCADE,
        related_name="security_check",
        db_column="shift_id",
    )

    # Bad if TRUE
    is_unknown_device_present = (
        models.BooleanField()
    )

    # Bad if TRUE
    is_unusual_behavior_observed = (
        models.BooleanField()
    )

    # Good if TRUE
    is_physically_secure = (
        models.BooleanField()
    )

    # Good if TRUE
    is_credentials_secure = (
        models.BooleanField()
    )

    # Bad if TRUE
    is_suspicious_surroundings = (
        models.BooleanField()
    )

    result = models.CharField(
        max_length=20,
        choices=Result.choices,
        db_index=True,
    )

    comments = models.TextField(
        blank=True
    )

    checked_at = models.DateTimeField(
        default=timezone.now
    )

    class Meta:

        db_table = (
            "daily_security_checks"
        )

    def calculate_result(self):

        suspicious = (
            self.is_unknown_device_present
            or
            self.is_unusual_behavior_observed
            or
            not self.is_physically_secure
            or
            not self.is_credentials_secure
            or
            self.is_suspicious_surroundings
        )

        if suspicious:

            return self.Result.SUSPICIOUS

        return self.Result.NORMAL

    def __str__(self):

        return (
            f"Security Check - "
            f"Shift {self.shift.shift_id}"
        )