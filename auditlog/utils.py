from .models import AuditLog


def get_client_ip(request):
    """
    Get the IP address directly seen by Django.
    """

    return request.META.get(
        "REMOTE_ADDR"
    )


def log_action(
    request,
    action,
    entity_type="",
    entity_id=None,
    details="",
):
    """
    Create a security audit record.
    """

    user = None

    if (
        hasattr(request, "user")
        and request.user.is_authenticated
    ):
        user = request.user

    AuditLog.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=get_client_ip(
            request
        ),
    )