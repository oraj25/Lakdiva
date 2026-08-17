from django.contrib import admin

from django.urls import (
    include,
    path,
)


urlpatterns = [

    # Django Admin
    path(
        "admin/",
        admin.site.urls,
    ),

    # Authentication / dashboards
    path(
        "",
        include(
            "accounts.urls"
        ),
    ),

    # Security Policy Management
    path(
        "",
        include(
            "policies.urls"
        ),
    ),
]