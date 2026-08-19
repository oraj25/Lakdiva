# Lakdiva SecurePOS

Lakdiva SecurePOS is a web-based security management system developed for Lakdiva Super.

The system supports security policy awareness, employee training, POS security checks, incident reporting, incident investigation, compliance monitoring, training needs identification, notifications, reporting, and audit logging.

---

# 1. Technology Stack

* Python 3.11
* Django 5.2
* MySQL 8
* HTML5
* CSS3
* JavaScript
* Git / GitHub

---

# 2. Application Roles

The system contains two application roles:

* `EMPLOYEE` — Employee
* `ADMIN` — Administrator

There is no separate Manager role in the final system. Administrator users perform the required management functions.

---

# 3. Main Features

Lakdiva SecurePOS includes:

* User authentication
* Role-based access control
* Employee management
* Administrator management
* Security policy management
* Policy acknowledgement
* Security awareness training
* Training assignments
* Security quizzes
* Quiz results
* POS terminal management
* POS shift management
* Daily POS security checks
* Shift handover
* Security incident reporting
* Incident categorisation
* Incident risk assessment
* Incident investigation
* Corrective actions
* Incident resolution
* Compliance monitoring
* Compliance summaries
* Training needs identification
* Administrator dashboard
* Notifications
* Security reports
* Audit logging
* Account management
* Secure password handling

---

# 4. Requirements

Before installing the project, make sure the following are installed:

* Python 3.11 or later
* MySQL 8.x
* Git
* pip
* A web browser

For Windows development, PowerShell can be used to run the commands shown below.

---

# 5. Clone the Repository

Clone the repository:

```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
```

Move into the project directory:

```bash
cd Lakdiva
```

If your repository folder has a different name, replace `Lakdiva` with the correct folder name.

---

# 6. Create a Virtual Environment

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If using Command Prompt:

```cmd
.venv\Scripts\activate
```

---

# 7. Install Python Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

---

# 8. Configure Environment Variables

Create a `.env` file in the project root.

If the repository contains `.env.example`, copy it:

```powershell
Copy-Item .env.example .env
```

The `.env` file should contain the configuration required by the Django project.

Example:

```env
DJANGO_SECRET_KEY=change-this-value
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=lakdiva_securepos_db
DB_USER=lakdiva_app
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=3306
```

Do **not** commit the real `.env` file to GitHub.

The `.env` file should be included in `.gitignore`.

---

# 9. Database Setup

Lakdiva SecurePOS uses MySQL.

The repository contains:

```text
database_setup.sql
```

This script is used to create the MySQL database and application database user.

Open MySQL Workbench or a MySQL command-line client and execute:

```bash
mysql -u root -p < database_setup.sql
```

Alternatively, open `database_setup.sql` in MySQL Workbench and execute the complete script.

After this step, the MySQL database required by the Django application should exist.

---

# 10. IMPORTANT — Initialize the Django Database

After the MySQL database has been created, run the following commands **in this exact order**.

## Step 1 — Run Django migrations

```bash
python manage.py migrate
```

This creates the Django application database tables.

Do not skip this step.

---

## Step 2 — Seed the predefined application data

After `migrate` has completed successfully, run:

```bash
python manage.py seed_initial_data
```

This creates the predefined data required for the initial Lakdiva SecurePOS installation.

Do **not** run `seed_initial_data` before `migrate`.

The correct order is:

```text
database_setup.sql
        ↓
MySQL database created
        ↓
python manage.py migrate
        ↓
Django tables created
        ↓
python manage.py seed_initial_data
        ↓
Predefined application data created
```

---

# 11. What `seed_initial_data` Creates

The command:

```bash
python manage.py seed_initial_data
```

creates the predefined application data required by the system.

## 11.1 Employee Role

The following role is created:

```text
EMPLOYEE
```

This role is used for normal Employee accounts.

---

## 11.2 Administrator Role

The following role is created:

```text
ADMIN
```

This role is used for Administrator accounts.

---

## 11.3 Default Administrator Account

A predefined Administrator account is created for development and demonstration purposes.

```text
Staff Number: ADM001
Full Name: System Administrator
Email: admin@lakdiva.local
Password: Admin@Lakdiva2026!
Role: ADMIN
Status: Active
```

Use this account to test Administrator functionality.

---

## 11.4 Demo Employee Account

A predefined Employee account is also created.

```text
Staff Number: EMP001
Full Name: Demo Employee
Email: employee@lakdiva.local
Password: Employee@Lakdiva2026!
Role: EMPLOYEE
Status: Active
```

Use this account to test Employee functionality.

---

## 11.5 POS Terminals

The following predefined POS terminals are created:

```text
POS-01
POS-02
POS-03
POS-04
```

These terminals are available for testing the POS security functionality.

---

## 11.6 Incident Categories

The initial incident categories are created automatically.

These include categories such as:

```text
Unauthorized Device
Suspicious Person
Password / Account Problem
Suspicious POS Activity
Malware
Data Exposure
Social Engineering
Other
```

These categories are available when an Employee reports a security incident.

---

# 12. Data That Is Not Automatically Seeded

The `seed_initial_data` command creates the required initial system data.

It does not create realistic operational records such as:

* Policies
* Training modules
* Quiz questions
* Training assignments
* Policy acknowledgements
* POS shifts
* Daily security checks
* Employee-reported incidents
* Incident investigations
* Incident risk assessments
* Corrective actions
* Compliance records
* Training needs
* Notifications
* Audit records

These records can be created through the application during testing and demonstration.

This allows the system to start with the required base configuration while allowing users to demonstrate the actual workflow themselves.

---

# 13. Verify the Installation

After running the migrations and seed command, run:

```bash
python manage.py check
```

A successful installation should report:

```text
System check identified no issues (0 silenced).
```

---

# 14. Start the Development Server

Run:

```bash
python manage.py runserver
```

The application should then be available at:

```text
http://127.0.0.1:8000/
```

Open the address in a web browser.

---

# 15. Development Login Accounts

## Administrator

```text
Staff Number: ADM001
Email: admin@lakdiva.local
Password: Admin@Lakdiva2026!
```

The Administrator account can be used to access the Administrator functionality.

---

## Employee

```text
Staff Number: EMP001
Email: employee@lakdiva.local
Password: Employee@Lakdiva2026!
```

The Employee account can be used to test Employee functionality.

---

# 16. Recommended Fresh Installation

For someone downloading the repository for the first time, the complete process is:

```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>

cd Lakdiva

python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the environment file:

```powershell
Copy-Item .env.example .env
```

Create the MySQL database:

```bash
mysql -u root -p < database_setup.sql
```

Then, **in this exact order**:

```bash
python manage.py migrate
```

```bash
python manage.py seed_initial_data
```

Verify Django:

```bash
python manage.py check
```

Start the application:

```bash
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

---

# 17. Installation Result

After completing the installation, the system should contain:

```text
MySQL Database
        ✓

Django Database Tables
        ✓

EMPLOYEE Role
        ✓

ADMIN Role
        ✓

Default Administrator
        ✓

Demo Employee
        ✓

POS-01
        ✓

POS-02
        ✓

POS-03
        ✓

POS-04
        ✓

Predefined Incident Categories
        ✓

Lakdiva SecurePOS
        ✓ Ready to use
```

---

# 18. Database Files

The repository contains database-related files for different purposes.

## `database_setup.sql`

Used to create the MySQL database and database user.

This is part of the initial installation process.

## `database_checks.sql`

Contains SQL queries that can be used to inspect and verify application data.

It is useful for:

* Checking users
* Checking roles
* Checking POS terminals
* Checking incidents
* Checking training records
* Checking compliance data
* Checking audit logs

`database_checks.sql` is **not** required to initialize the application.

Django migrations are responsible for creating the application tables.

---

# 19. Security Considerations

The repository is intended for development, academic demonstration, and controlled testing.

The predefined credentials are development/demo credentials only.

For production deployment:

* Change all default passwords.
* Generate a new Django secret key.
* Set `DEBUG=False`.
* Configure `ALLOWED_HOSTS` correctly.
* Use HTTPS.
* Use secure cookies.
* Use a strong MySQL password.
* Do not expose MySQL directly to the Internet.
* Do not commit `.env`.
* Restrict database permissions.
* Protect uploaded incident evidence.
* Keep dependencies updated.
* Review audit logs regularly.

---

# 20. Important GitHub Security Rule

Never commit:

```text
.env
```

to GitHub.

The repository should contain:

```text
.env.example
```

instead.

`.env.example` should contain placeholder values rather than real production secrets.

---

# 21. Project Structure

A typical project structure is:

```text
Lakdiva/
│
├── accounts/
├── auditlog/
├── compliance/
├── core/
├── incidents/
├── notifications/
├── policies/
├── pos_security/
├── reports/
├── training/
├── training_needs/
│
├── static/
├── templates/
├── media/
│
├── database_setup.sql
├── database_checks.sql
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── manage.py
```

The exact structure may change as the project is developed.

---

# 22. Application Workflow

The main security-management workflow is:

```text
Security Policies
        ↓
Employee Awareness
        ↓
Security Training
        ↓
Security Quiz
        ↓
POS Security Checks
        ↓
Incident Reporting
        ↓
Incident Risk Assessment
        ↓
Incident Investigation
        ↓
Corrective Action
        ↓
Incident Resolution
        ↓
Compliance Monitoring
        ↓
Training Needs Identification
        ↓
Management Reporting
        ↓
Audit and Continuous Improvement
```

---

# 23. Purpose of the System

Lakdiva SecurePOS is designed to provide a centralized platform for managing information security awareness and operational security activities within a supermarket environment.

Employees can interact with security policies, complete training, perform POS security checks, report incidents, and monitor their own security responsibilities.

Administrators can manage the overall security process, investigate incidents, assess risks, monitor compliance, identify training needs, review reports, and maintain audit records.

---

# 24. Quick Start

If the database has already been created and the Python dependencies are installed, the most important commands are simply:

```bash
python manage.py migrate
```

Then:

```bash
python manage.py seed_initial_data
```

Then:

```bash
python manage.py runserver
```

The predefined roles, accounts, POS terminals, and incident categories will be available after `seed_initial_data` completes successfully.
