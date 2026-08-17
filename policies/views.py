from django.contrib import messages

from django.contrib.auth import (
    get_user_model,
)

from django.db import transaction

from django.db.models import Q

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from django.views.decorators.http import (
    require_POST,
)

from accounts.decorators import (
    role_required,
)

from accounts.models import Role

from auditlog.utils import (
    log_action,
)

from .forms import (
    NewPolicyVersionForm,
    PolicyForm,
)

from .models import (
    EMPLOYEE_POLICY_TYPES,
    Policy,
    PolicyAcknowledgement,
)


User = get_user_model()


# =========================================================
# HELPER
# =========================================================

def suggest_next_version(version):
    """
    Convert:
    1.0 -> 1.1
    1.1 -> 1.2
    2.0 -> 2.1

    Admin can still change the suggestion.
    """

    try:

        parts = version.split(".")

        if len(parts) == 1:
            return f"{int(parts[0]) + 1}.0"

        parts[-1] = str(
            int(parts[-1]) + 1
        )

        return ".".join(parts)

    except (
        ValueError,
        AttributeError,
    ):
        return "1.0"


# =========================================================
# ADMIN - POLICY LIST
# =========================================================

@role_required(Role.ADMIN)
def admin_policy_list(request):

    policies = (
        Policy.objects
        .select_related(
            "created_by"
        )
        .all()
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    policy_type = request.GET.get(
        "type",
        "",
    ).strip()

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    if search:

        policies = policies.filter(
            Q(
                title__icontains=search
            )
            |
            Q(
                version__icontains=search
            )
            |
            Q(
                policy_type__icontains=search
            )
        )

    # -----------------------------------------------------
    # STATUS FILTER
    # -----------------------------------------------------

    if status:

        policies = policies.filter(
            status=status
        )

    # -----------------------------------------------------
    # TYPE FILTER
    # -----------------------------------------------------

    if policy_type:

        policies = policies.filter(
            policy_type=policy_type
        )

    context = {

        "policies": policies,

        "search": search,

        "selected_status": status,

        "selected_type": policy_type,

        "statuses": (
            Policy.Status.choices
        ),

        "policy_types": (
            Policy.PolicyType.choices
        ),
    }

    return render(
        request,
        "administrator/policies/list.html",
        context,
    )


# =========================================================
# ADMIN - CREATE POLICY
# =========================================================

@role_required(Role.ADMIN)
def admin_policy_create(request):

    form = PolicyForm(
        request.POST or None
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        policy = form.save(
            commit=False
        )

        policy.created_by = (
            request.user
        )

        policy.status = (
            Policy.Status.DRAFT
        )

        policy.save()

        log_action(
            request=request,
            action="POLICY_CREATED",
            entity_type="Policy",
            entity_id=policy.policy_id,
            details=(
                f"Created policy "
                f"'{policy.title}' "
                f"version {policy.version} "
                f"as Draft."
            ),
        )

        messages.success(
            request,
            (
                "Policy created successfully "
                "as Draft."
            ),
        )

        return redirect(
            "policies:admin_detail",
            policy_id=policy.policy_id,
        )

    return render(
        request,
        "administrator/policies/form.html",
        {
            "form": form,
            "page_title": (
                "Create Security Policy"
            ),
            "button_text": (
                "Create Draft"
            ),
        },
    )


# =========================================================
# ADMIN - POLICY DETAIL
# =========================================================

@role_required(Role.ADMIN)
def admin_policy_detail(
    request,
    policy_id,
):

    policy = get_object_or_404(
        Policy.objects.select_related(
            "created_by"
        ),
        policy_id=policy_id,
    )

    # Active employees only
    employees = User.objects.filter(
        role__role_name=Role.EMPLOYEE,
        status=User.Status.ACTIVE,
    )

    total_employees = (
        employees.count()
    )

    acknowledgement_count = (
        PolicyAcknowledgement
        .objects
        .filter(
            policy=policy,
            user__in=employees,
        )
        .count()
    )

    pending_count = max(
        total_employees
        - acknowledgement_count,
        0,
    )

    context = {

        "policy": policy,

        "total_employees": (
            total_employees
        ),

        "acknowledgement_count": (
            acknowledgement_count
        ),

        "pending_count": (
            pending_count
        ),
    }

    return render(
        request,
        (
            "administrator/"
            "policies/detail.html"
        ),
        context,
    )


# =========================================================
# ADMIN - EDIT DRAFT
# =========================================================

@role_required(Role.ADMIN)
def admin_policy_edit(
    request,
    policy_id,
):

    policy = get_object_or_404(
        Policy,
        policy_id=policy_id,
    )

    # Published/archived policies
    # must not be directly modified.
    if (
        policy.status
        != Policy.Status.DRAFT
    ):

        messages.error(
            request,
            (
                "Only Draft policies can "
                "be edited. Create a new "
                "version instead."
            ),
        )

        return redirect(
            "policies:admin_detail",
            policy_id=policy.policy_id,
        )

    form = PolicyForm(
        request.POST or None,
        instance=policy,
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        policy = form.save()

        log_action(
            request=request,
            action="POLICY_UPDATED",
            entity_type="Policy",
            entity_id=policy.policy_id,
            details=(
                f"Updated Draft policy "
                f"'{policy.title}' "
                f"version {policy.version}."
            ),
        )

        messages.success(
            request,
            "Draft policy updated.",
        )

        return redirect(
            "policies:admin_detail",
            policy_id=policy.policy_id,
        )

    return render(
        request,
        "administrator/policies/form.html",
        {
            "form": form,
            "policy": policy,
            "page_title": (
                "Edit Security Policy"
            ),
            "button_text": (
                "Save Changes"
            ),
        },
    )


# =========================================================
# ADMIN - PUBLISH
# =========================================================

@role_required(Role.ADMIN)
@require_POST
def admin_policy_publish(
    request,
    policy_id,
):

    with transaction.atomic():

        policy = get_object_or_404(
            Policy.objects.select_for_update(),
            policy_id=policy_id,
        )

        if (
            policy.status
            != Policy.Status.DRAFT
        ):

            messages.error(
                request,
                (
                    "Only a Draft policy "
                    "can be published."
                ),
            )

            return redirect(
                "policies:admin_detail",
                policy_id=policy.policy_id,
            )

        # -------------------------------------------------
        # Archive previous published versions
        # with the same policy title.
        # -------------------------------------------------

        previous_versions = list(
            Policy.objects
            .select_for_update()
            .filter(
                title=policy.title,
                status=(
                    Policy.Status.PUBLISHED
                ),
            )
            .exclude(
                policy_id=policy.policy_id
            )
            .values_list(
                "policy_id",
                flat=True,
            )
        )

        if previous_versions:

            Policy.objects.filter(
                policy_id__in=(
                    previous_versions
                )
            ).update(
                status=(
                    Policy.Status.ARCHIVED
                )
            )

        # -------------------------------------------------
        # Publish current version
        # -------------------------------------------------

        policy.status = (
            Policy.Status.PUBLISHED
        )

        policy.save(
            update_fields=[
                "status"
            ]
        )

    log_action(
        request=request,
        action="POLICY_PUBLISHED",
        entity_type="Policy",
        entity_id=policy.policy_id,
        details=(
            f"Published policy "
            f"'{policy.title}' "
            f"version {policy.version}."
        ),
    )

    messages.success(
        request,
        (
            f"{policy.title} "
            f"version {policy.version} "
            f"has been published."
        ),
    )

    return redirect(
        "policies:admin_detail",
        policy_id=policy.policy_id,
    )


# =========================================================
# ADMIN - ARCHIVE
# =========================================================

@role_required(Role.ADMIN)
@require_POST
def admin_policy_archive(
    request,
    policy_id,
):

    policy = get_object_or_404(
        Policy,
        policy_id=policy_id,
    )

    if (
        policy.status
        != Policy.Status.PUBLISHED
    ):

        messages.error(
            request,
            (
                "Only a published policy "
                "can be archived."
            ),
        )

        return redirect(
            "policies:admin_detail",
            policy_id=policy.policy_id,
        )

    policy.status = (
        Policy.Status.ARCHIVED
    )

    policy.save(
        update_fields=[
            "status"
        ]
    )

    log_action(
        request=request,
        action="POLICY_ARCHIVED",
        entity_type="Policy",
        entity_id=policy.policy_id,
        details=(
            f"Archived policy "
            f"'{policy.title}' "
            f"version {policy.version}."
        ),
    )

    messages.success(
        request,
        "Policy archived successfully.",
    )

    return redirect(
        "policies:admin_detail",
        policy_id=policy.policy_id,
    )


# =========================================================
# ADMIN - CREATE NEW VERSION
# =========================================================

@role_required(Role.ADMIN)
def admin_policy_new_version(
    request,
    policy_id,
):

    source_policy = (
        get_object_or_404(
            Policy,
            policy_id=policy_id,
        )
    )

    if (
        source_policy.status
        == Policy.Status.DRAFT
    ):

        messages.warning(
            request,
            (
                "This policy is already "
                "a Draft. Edit it instead."
            ),
        )

        return redirect(
            "policies:admin_edit",
            policy_id=(
                source_policy.policy_id
            ),
        )

    initial_version = (
        suggest_next_version(
            source_policy.version
        )
    )

    form = NewPolicyVersionForm(
        request.POST or None,
        initial={
            "version": initial_version
        },
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        new_version = (
            form.cleaned_data[
                "version"
            ]
        )

        # Prevent duplicate version
        if Policy.objects.filter(
            title__iexact=(
                source_policy.title
            ),
            version=new_version,
        ).exists():

            form.add_error(
                "version",
                (
                    "This version already "
                    "exists for this policy."
                ),
            )

        else:

            new_policy = Policy(
                title=(
                    source_policy.title
                ),
                policy_type=(
                    source_policy.policy_type
                ),
                version=new_version,
                content=(
                    source_policy.content
                ),
                effective_date=None,
                review_date=None,
                status=(
                    Policy.Status.DRAFT
                ),
                created_by=request.user,
            )

            new_policy.full_clean()

            new_policy.save()

            log_action(
                request=request,
                action=(
                    "POLICY_VERSION_CREATED"
                ),
                entity_type="Policy",
                entity_id=(
                    new_policy.policy_id
                ),
                details=(
                    f"Created version "
                    f"{new_policy.version} "
                    f"from "
                    f"{source_policy.title} "
                    f"version "
                    f"{source_policy.version}."
                ),
            )

            messages.success(
                request,
                (
                    "New Draft version "
                    "created. Review and edit "
                    "it before publishing."
                ),
            )

            return redirect(
                "policies:admin_edit",
                policy_id=(
                    new_policy.policy_id
                ),
            )

    return render(
        request,
        (
            "administrator/"
            "policies/new_version.html"
        ),
        {
            "form": form,
            "policy": source_policy,
        },
    )


# =========================================================
# EMPLOYEE - POLICY LIST
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_policy_list(
    request,
):

    policies = Policy.objects.filter(
        status=Policy.Status.PUBLISHED,
        policy_type__in=(
            EMPLOYEE_POLICY_TYPES
        ),
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    policy_type = request.GET.get(
        "type",
        "",
    ).strip()

    if search:

        policies = policies.filter(
            Q(
                title__icontains=search
            )
            |
            Q(
                content__icontains=search
            )
        )

    if policy_type:

        policies = policies.filter(
            policy_type=policy_type
        )

    acknowledged_ids = list(
        PolicyAcknowledgement.objects
        .filter(
            user=request.user,
            policy__in=policies,
        )
        .values_list(
            "policy_id",
            flat=True,
        )
    )

    total_count = (
        policies.count()
    )

    acknowledged_count = len(
        acknowledged_ids
    )

    pending_count = max(
        total_count
        - acknowledged_count,
        0,
    )

    return render(
        request,
        "employee/policies/list.html",
        {
            "policies": policies,

            "acknowledged_ids": (
                acknowledged_ids
            ),

            "total_count": (
                total_count
            ),

            "acknowledged_count": (
                acknowledged_count
            ),

            "pending_count": (
                pending_count
            ),

            "search": search,

            "selected_type": (
                policy_type
            ),

            "policy_types": [
                choice
                for choice
                in Policy.PolicyType.choices
                if choice[0]
                in EMPLOYEE_POLICY_TYPES
            ],
        },
    )


# =========================================================
# EMPLOYEE - POLICY DETAIL
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_policy_detail(
    request,
    policy_id,
):

    policy = get_object_or_404(
        Policy,
        policy_id=policy_id,
        status=(
            Policy.Status.PUBLISHED
        ),
        policy_type__in=(
            EMPLOYEE_POLICY_TYPES
        ),
    )

    acknowledgement = (
        PolicyAcknowledgement
        .objects
        .filter(
            policy=policy,
            user=request.user,
        )
        .first()
    )

    return render(
        request,
        (
            "employee/"
            "policies/detail.html"
        ),
        {
            "policy": policy,

            "acknowledgement": (
                acknowledgement
            ),
        },
    )


# =========================================================
# EMPLOYEE - ACKNOWLEDGE
# =========================================================

@role_required(Role.EMPLOYEE)
@require_POST
def employee_policy_acknowledge(
    request,
    policy_id,
):

    policy = get_object_or_404(
        Policy,
        policy_id=policy_id,
        status=(
            Policy.Status.PUBLISHED
        ),
        policy_type__in=(
            EMPLOYEE_POLICY_TYPES
        ),
    )

    # Require explicit confirmation
    if (
        request.POST.get("confirm")
        != "yes"
    ):

        messages.error(
            request,
            (
                "Please confirm that you "
                "have read and understood "
                "the policy."
            ),
        )

        return redirect(
            "policies:employee_detail",
            policy_id=policy.policy_id,
        )

    acknowledgement, created = (
        PolicyAcknowledgement
        .objects
        .get_or_create(
            policy=policy,
            user=request.user,
        )
    )

    if created:

        log_action(
            request=request,
            action=(
                "POLICY_ACKNOWLEDGED"
            ),
            entity_type="Policy",
            entity_id=policy.policy_id,
            details=(
                f"Employee "
                f"{request.user.staff_no} "
                f"acknowledged "
                f"'{policy.title}' "
                f"version {policy.version}."
            ),
        )

        messages.success(
            request,
            (
                "Policy acknowledgement "
                "recorded successfully."
            ),
        )

    else:

        messages.warning(
            request,
            (
                "You have already "
                "acknowledged this policy."
            ),
        )

    return redirect(
        "policies:employee_detail",
        policy_id=policy.policy_id,
    )