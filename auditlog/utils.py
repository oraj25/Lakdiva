from .models import (
    AuditLog,
)


# =========================================================
# CLIENT IP
# =========================================================

def get_client_ip(
    request,
):

    if not request:

        return None

    return request.META.get(
        "REMOTE_ADDR"
    )


# =========================================================
# CREATE AUDIT LOG
# =========================================================

def log_action(
    request,
    action,
    entity_type="",
    entity_id=None,
    details="",
    user=None,
):

    # -----------------------------------------------------
    # DETERMINE ACTOR
    # -----------------------------------------------------

    actor = user

    if actor is None:

        request_user = getattr(
            request,
            "user",
            None,
        )

        if (
            request_user
            and
            request_user.is_authenticated
        ):

            actor = request_user


    # -----------------------------------------------------
    # CREATE AUDIT RECORD
    # -----------------------------------------------------

    return AuditLog.objects.create(

        user=actor,

        action=str(
            action
        )[:100],

        entity_type=str(
            entity_type or ""
        )[:100],

        entity_id=entity_id,

        details=str(
            details or ""
        ),

        ip_address=(
            get_client_ip(
                request
            )
        ),
    )