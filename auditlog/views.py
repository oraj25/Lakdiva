from django.core.paginator import (
    Paginator,
)

from django.db.models import Q

from django.shortcuts import (
    get_object_or_404,
    render,
)

from django.utils import timezone

from django.views.decorators.http import (
    require_GET,
)

from accounts.decorators import (
    role_required,
)

from accounts.models import (
    Role,
)

from .forms import (
    AuditLogFilterForm,
)

from .models import (
    AuditLog,
)

from .utils import (
    log_action,
)


# =========================================================
# ADMIN - AUDIT LOG LIST
# =========================================================

@role_required(Role.ADMIN)
@require_GET
def admin_audit_log_list(
    request,
):

    logs = (
        AuditLog.objects
        .select_related(
            "user",
        )
        .all()
    )


    form = AuditLogFilterForm(
        request.GET or None
    )


    # =====================================================
    # FILTERS
    # =====================================================

    if form.is_valid():

        search = (
            form.cleaned_data.get(
                "search"
            )
        )

        user = (
            form.cleaned_data.get(
                "user"
            )
        )

        action = (
            form.cleaned_data.get(
                "action"
            )
        )

        entity_type = (
            form.cleaned_data.get(
                "entity_type"
            )
        )

        date_from = (
            form.cleaned_data.get(
                "date_from"
            )
        )

        date_to = (
            form.cleaned_data.get(
                "date_to"
            )
        )


        # -------------------------------------------------
        # SEARCH
        # -------------------------------------------------

        if search:

            logs = logs.filter(

                Q(
                    action__icontains=(
                        search
                    )
                )

                |

                Q(
                    entity_type__icontains=(
                        search
                    )
                )

                |

                Q(
                    details__icontains=(
                        search
                    )
                )

                |

                Q(
                    ip_address__icontains=(
                        search
                    )
                )

                |

                Q(
                    user__staff_no__icontains=(
                        search
                    )
                )

                |

                Q(
                    user__full_name__icontains=(
                        search
                    )
                )
            )


        # -------------------------------------------------
        # USER
        # -------------------------------------------------

        if user:

            logs = logs.filter(
                user=user
            )


        # -------------------------------------------------
        # ACTION
        # -------------------------------------------------

        if action:

            logs = logs.filter(
                action=action
            )


        # -------------------------------------------------
        # ENTITY
        # -------------------------------------------------

        if entity_type:

            logs = logs.filter(
                entity_type=(
                    entity_type
                )
            )


        # -------------------------------------------------
        # DATE FROM
        # -------------------------------------------------

        if date_from:

            logs = logs.filter(
                created_at__date__gte=(
                    date_from
                )
            )


        # -------------------------------------------------
        # DATE TO
        # -------------------------------------------------

        if date_to:

            logs = logs.filter(
                created_at__date__lte=(
                    date_to
                )
            )


    # =====================================================
    # SUMMARY COUNTS
    # =====================================================

    filtered_count = (
        logs.count()
    )

    total_count = (
        AuditLog.objects.count()
    )

    today = (
        timezone.localdate()
    )

    today_count = (
        AuditLog.objects
        .filter(
            created_at__date=today
        )
        .count()
    )

    system_event_count = (
        AuditLog.objects
        .filter(
            user__isnull=True
        )
        .count()
    )


    # =====================================================
    # PAGINATION
    # =====================================================

    paginator = Paginator(
        logs,
        50,
    )

    page_number = (
        request.GET.get(
            "page"
        )
    )

    page_obj = (
        paginator.get_page(
            page_number
        )
    )


    # Keep active filters when moving
    # to the next/previous page.

    query_params = (
        request.GET.copy()
    )

    query_params.pop(
        "page",
        None,
    )

    filter_query = (
        query_params.urlencode()
    )


    # =====================================================
    # RENDER
    # =====================================================

    return render(
        request,
        (
            "administrator/"
            "auditlog/list.html"
        ),
        {
            "form": form,

            "page_obj": (
                page_obj
            ),

            "logs": (
                page_obj.object_list
            ),

            "filtered_count": (
                filtered_count
            ),

            "total_count": (
                total_count
            ),

            "today_count": (
                today_count
            ),

            "system_event_count": (
                system_event_count
            ),

            "filter_query": (
                filter_query
            ),
        },
    )


# =========================================================
# ADMIN - AUDIT LOG DETAIL
# =========================================================

@role_required(Role.ADMIN)
@require_GET
def admin_audit_log_detail(
    request,
    log_id,
):

    audit_entry = get_object_or_404(

        AuditLog.objects
        .select_related(
            "user"
        ),

        log_id=log_id,
    )


    # Record review of an individual
    # sensitive audit event.

    log_action(
        request=request,

        action=(
            "AUDIT_LOG_REVIEWED"
        ),

        entity_type=(
            "AuditLog"
        ),

        entity_id=(
            audit_entry.log_id
        ),

        details=(
            f"Administrator "
            f"{request.user.staff_no} "
            f"reviewed audit log "
            f"{audit_entry.log_id}."
        ),
    )


    return render(
        request,
        (
            "administrator/"
            "auditlog/detail.html"
        ),
        {
            "audit_entry": (
                audit_entry
            ),
        },
    )