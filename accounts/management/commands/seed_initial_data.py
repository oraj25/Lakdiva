import os

from django.core.management.base import (
    BaseCommand,
)

from accounts.models import (
    Role,
    User,
)

from incidents.models import (
    IncidentCategory,
)

from pos_security.models import (
    POSTerminal,
)


# =========================================================
# INITIAL LAKDIVA SECUREPOS DATA
# =========================================================

class Command(BaseCommand):

    help = (
        "Create the initial Lakdiva SecurePOS "
        "roles, users, POS terminals and "
        "incident categories."
    )


    def handle(
        self,
        *args,
        **options,
    ):

        self.stdout.write(
            "Creating Lakdiva SecurePOS "
            "initial data..."
        )


        # =================================================
        # ROLES
        # =================================================

        employee_role, _ = (
            Role.objects.get_or_create(
                role_name=(
                    Role.EMPLOYEE
                )
            )
        )

        admin_role, _ = (
            Role.objects.get_or_create(
                role_name=(
                    Role.ADMIN
                )
            )
        )


        self.stdout.write(
            self.style.SUCCESS(
                "Roles ready."
            )
        )


        # =================================================
        # DEFAULT ADMINISTRATOR
        # =================================================

        admin_email = os.getenv(
            "DEFAULT_ADMIN_EMAIL",
            "admin@lakdiva.local",
        )

        admin_staff_no = os.getenv(
            "DEFAULT_ADMIN_STAFF_NO",
            "ADM001",
        )

        admin_full_name = os.getenv(
            "DEFAULT_ADMIN_FULL_NAME",
            "System Administrator",
        )

        admin_password = os.getenv(
            "DEFAULT_ADMIN_PASSWORD",
            "Admin@Lakdiva2026!",
        )


        admin_user = (
            User.objects
            .filter(
                email__iexact=(
                    admin_email
                )
            )
            .first()
        )


        if admin_user is None:

            admin_user = (
                User.objects.create_superuser(

                    email=admin_email,

                    staff_no=(
                        admin_staff_no
                    ),

                    full_name=(
                        admin_full_name
                    ),

                    password=(
                        admin_password
                    ),
                )
            )


            self.stdout.write(
                self.style.SUCCESS(
                    (
                        "Default administrator "
                        "created."
                    )
                )
            )

        else:

            # Ensure an existing seeded
            # administrator remains consistent.

            changed = False

            if (
                admin_user.role_id
                != admin_role.role_id
            ):

                admin_user.role = (
                    admin_role
                )

                changed = True


            if not admin_user.is_staff:

                admin_user.is_staff = True

                changed = True


            if not admin_user.is_superuser:

                admin_user.is_superuser = True

                changed = True


            if (
                admin_user.status
                != User.Status.ACTIVE
            ):

                admin_user.status = (
                    User.Status.ACTIVE
                )

                changed = True


            if changed:

                admin_user.save()


            self.stdout.write(
                "Default administrator "
                "already exists."
            )


        # =================================================
        # OPTIONAL DEMO EMPLOYEE
        # =================================================

        employee_email = os.getenv(
            "DEFAULT_EMPLOYEE_EMAIL",
            "employee@lakdiva.local",
        )

        employee_staff_no = os.getenv(
            "DEFAULT_EMPLOYEE_STAFF_NO",
            "EMP001",
        )

        employee_full_name = os.getenv(
            "DEFAULT_EMPLOYEE_FULL_NAME",
            "Demo Employee",
        )

        employee_password = os.getenv(
            "DEFAULT_EMPLOYEE_PASSWORD",
            "Employee@Lakdiva2026!",
        )


        if not User.objects.filter(
            email__iexact=(
                employee_email
            )
        ).exists():

            User.objects.create_user(

                email=employee_email,

                staff_no=(
                    employee_staff_no
                ),

                full_name=(
                    employee_full_name
                ),

                password=(
                    employee_password
                ),

                role=employee_role,

                status=(
                    User.Status.ACTIVE
                ),

                is_staff=False,
            )


            self.stdout.write(
                self.style.SUCCESS(
                    "Demo employee created."
                )
            )

        else:

            self.stdout.write(
                "Demo employee already exists."
            )


        # =================================================
        # POS TERMINALS
        # =================================================

        terminal_codes = [
            "POS-01",
            "POS-02",
            "POS-03",
            "POS-04",
        ]


        for terminal_code in terminal_codes:

            POSTerminal.objects.get_or_create(

                terminal_code=(
                    terminal_code
                ),

                defaults={
                    "status": (
                        POSTerminal
                        .Status
                        .ACTIVE
                    ),
                },
            )


        self.stdout.write(
            self.style.SUCCESS(
                "POS terminals ready."
            )
        )


        # =================================================
        # INCIDENT CATEGORIES
        # =================================================

        categories = [

            (
                "Unauthorized Device",
                (
                    "Unknown or unauthorized "
                    "USB, removable media or "
                    "other device."
                ),
            ),

            (
                "Suspicious Person",
                (
                    "Suspicious or unauthorized "
                    "person observed near a POS "
                    "terminal or protected area."
                ),
            ),

            (
                "Password / Account Problem",
                (
                    "Password compromise, "
                    "account misuse or "
                    "authentication concern."
                ),
            ),

            (
                "Suspicious POS Activity",
                (
                    "Unexpected or suspicious "
                    "POS terminal behaviour."
                ),
            ),

            (
                "Malware",
                (
                    "Suspected malicious "
                    "software or malware."
                ),
            ),

            (
                "Data Exposure",
                (
                    "Possible exposure or "
                    "unauthorized disclosure "
                    "of information."
                ),
            ),

            (
                "Social Engineering",
                (
                    "Phishing, impersonation "
                    "or other social-engineering "
                    "attempt."
                ),
            ),

            (
                "Other",
                (
                    "Security concern not "
                    "covered by another category."
                ),
            ),
        ]


        for (
            category_name,
            description,
        ) in categories:

            IncidentCategory.objects.get_or_create(

                category_name=(
                    category_name
                ),

                defaults={

                    "description": (
                        description
                    ),

                    "status": (
                        IncidentCategory
                        .Status
                        .ACTIVE
                    ),
                },
            )


        self.stdout.write(
            self.style.SUCCESS(
                "Incident categories ready."
            )
        )


        # =================================================
        # COMPLETE
        # =================================================

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Lakdiva SecurePOS initial "
                    "data setup completed."
                )
            )
        )