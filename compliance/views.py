from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from django.shortcuts import (
    get_object_or_404,
    render,
)

from accounts.decorators import role_required
from accounts.models import Role

from .models import ComplianceSummary

from .services import (
    calculate_user_compliance,
)


# =========================================================
# EMPLOYEE - MY COMPLIANCE
# =========================================================

@login_required
def my_compliance(request):

    summary = calculate_user_compliance(
        request.user
    )

    return render(
        request,
        "compliance/my_compliance.html",
        {
            "summary": summary,
        },
    )


# =========================================================
# ADMIN - COMPLIANCE DASHBOARD
# =========================================================

@role_required(Role.ADMIN)
@login_required
def admin_compliance(request):

    summaries = (
        ComplianceSummary.objects
        .select_related("user")
        .order_by("-employee_score")
    )

    return render(
        request,
        "compliance/admin_compliance.html",
        {
            "summaries": summaries,
        },
    )


# =========================================================
# ADMIN - EMPLOYEE COMPLIANCE DETAILS
# =========================================================

@role_required(Role.ADMIN)
@login_required
def admin_employee_compliance(request, user_id):

    User = get_user_model()

    employee = get_object_or_404(
        User,
        pk=user_id,
    )

    summary = calculate_user_compliance(
        employee
    )

    return render(
        request,
        "compliance/employee_detail.html",
        {
            "employee": employee,
            "summary": summary,
        },
    )