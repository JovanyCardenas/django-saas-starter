# Django SaaS Starter Template

A reusable Django starter template for building multiple standalone web apps with consistent foundations:
- Email-based authentication (custom User model)
- Role-based access control (RBAC)
- Optional multi-tenant support (schools/orgs/chapters/etc.)
- Audit logging
- In-app notifications
- File uploads (local dev; cloud-ready)
- Clean UI shell (Tailwind)

This repository is meant to be **cloned** into product-specific repos (e.g., College Corps Platform, SkillsUSA HQ).  
Each product will have **its own users, database, deployment, and domain**. No shared logins across products.

---

## Tech Stack

- **Backend:** Django + PostgreSQL
- **Auth:** Custom User model (email login)
- **Static Files:** WhiteNoise (production)
- **Config:** `python-dotenv` + `dj-database-url`
- **UI:** Django templates + Tailwind (CDN by default)
- **Optional later:** Celery/Huey for background jobs; S3/R2 for file storage

---

## Project Structure

backend/<br>
│<br>
├── config/<br>
│   ├── settings.py<br>
│   ├── urls.py<br>
│<br>
├── apps/<br>
│   ├── accounts/        # authentication + user model<br>
│   ├── tenants/         # orgs + memberships + middleware<br>
│   ├── rbac/            # roles + permissions<br>
│   ├── auditlog/        # audit tracking<br>
│   ├── notifications/   # in-app notifications (foundation)<br>
│   ├── files/           # file uploads<br>
│   ├── settings_panel/  # org settings, members, roles UI<br>
│   ├── dashboard/       # main app entry point<br>
│<br>
├── templates/<br>
├── static/<br>
├── manage.py<br>
├── requirements.txt<br>

### Apps Overview

#### `apps/accounts`
- Custom `User` model (email as primary identifier)
- Login/logout/password reset
- Profile basics

#### `apps/rbac`
- Simple RBAC primitives:
  - Roles (e.g., Admin, Staff, Member)
  - Permission strings (e.g., `applications.review`)
- Helpers/decorators for view protection
- Role assignment per tenant

#### `apps/tenants`
- Tenant models for organizations/schools/programs
- Membership mapping users to tenants
- Middleware to attach `request.tenant`
- Utilities for tenant scoping
- Supports multi-organization users

> Products can choose to use tenants (College Corps and SkillsUSA likely will).

#### `apps/settings_panel`
- Organization settings UI
- Member management
- Role management
- Invitation system

#### `apps/auditlog`
- Central logging system
- Tracks:
  - membership changes
  - role assignments
  - file uploads
  - organization updates

#### `apps/notifications`
- In-app notifications (`read_at` tracking)
- Helper functions to create notifications
- Read/unread tracking

#### `apps/files`
- File uploads + metadata
- Local storage in dev; cloud-ready pattern for prod
- Tenant-scoped file uploads
- Metadata + categories
- Soft delete (deactivate)

---

## Getting Started

### 1) Requirements
- Python 3.10+ recommended
- PostgreSQL recommended (SQLite can be used in dev if configured)

### 2) Setup

```bash
cd backend
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3) Create environment file

```bash
cp .example.env .env
# (or use the legacy filename: cp .env.example .env)
```
Edit ``.env`` if needed.

### 4) Run migrations

```bash
python manage.py migrate
```

### 5) Create Superuser

```bash
python manage.py createsuperuser
```

### 6) Bootstrap your first organization

```bash
python manage.py bootstrap_tenant "My Organization" 
  --slug my-org 
  --owner-email your@email.com 
  --owner-password TempPass123!
```

This will:

- Create tenant
- Create user (if needed)
- Add membership
- Seed RBAC roles
- Assign owner role

### 7) Run server

```bash
python manage.py runserver
```
Open:
```
http://127.0.0.1:8000/
```
---
### Usefull Commands

```bash
# Create tenant
python manage.py create_tenant "Test Org" --slug test-org --if-exists reuse

# Add membership
python manage.py add_membership test-org user@email.com --role owner

# Seed RBAC roles
python manage.py seed_rbac test-org

# Assign RBAC role
python manage.py assign_role test-org user@email.com owner --replace

# Run tests
python manage.py test
```

---

### Main Pages

```
/                       Dashboard
/accounts/login/        Login
/tenants/choose/        Select organization
/settings/organization/ Organization settings
/settings/members/      Member management
/settings/roles/        RBAC roles
/files/                 File uploads
/audit/                 Audit log
/admin/                 Django admin
```

---

### Notes
- **CSRF errors in dev?**<br>
  Add to .env:
  ```
  DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
  ```
- **File uploads**<br>
  Store locally in dev (``/media/``), cloud-ready for production
- **Tenants**<br>
  Everything is scoped to ``request.tenant``

---

### Next Steps (Project Roadmap)

- Notification UI
- File permissions
- Activity dashboard
- API layer (Django REST Framework)
- Background jobs (Celery/Redis)
- Production deployment (Render / Docker)

--- 

### Purpose
This template exists so you can:
- Build apps faster
- Reuse a solid SaaS foundation
- Avoid rebuilding auth, RBAC, tenants, etc. everytime
