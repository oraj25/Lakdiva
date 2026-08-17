from django.contrib import admin

from django.urls import (
    include,
    path,
)


urlpatterns = [

    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "",
        include(
            "accounts.urls"
        ),
    ),

    path(
        "",
        include(
            "policies.urls"
        ),
    ),

    path(
        "",
        include(
            "training.urls"
        ),
    ),

    path(
        "",
        include(
            "pos_security.urls"
        ),
    ),

    path(
        "",
        include(
            "incidents.urls"
        ),
    ),
]