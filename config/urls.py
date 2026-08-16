from django.contrib import admin

from django.urls import (
    include,
    path,
)


urlpatterns = [

    # Django development/admin panel
    path(
        "admin/",
        admin.site.urls,
    ),

    # Lakdiva SecurePOS
    path(
        "",
        include("accounts.urls"),
    ),
]