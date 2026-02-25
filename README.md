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
backend/
config/
settings/
base.py
dev.py
prod.py
apps/
accounts/        # custom User model, auth flows
rbac/            # roles + permissions helpers
tenants/         # optional multi-tenant models + middleware
auditlog/        # audit events
notifications/   # in-app notifications
files/           # uploads + file metadata
templates/
static/
manage.py
requirements.txt
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

#### `apps/tenants` (optional)
- Tenant models for organizations/schools/programs
- Membership mapping users to tenants
- Middleware to attach `request.tenant`
- Utilities for tenant scoping

> Products can choose to use tenants (College Corps and SkillsUSA likely will).

#### `apps/auditlog`
- Central audit event store
- Helper to log events consistently

#### `apps/notifications`
- In-app notifications (`read_at` tracking)
- Helper functions to create notifications

#### `apps/files`
- File uploads + metadata
- Local storage in dev; cloud-ready pattern for prod

---

## Getting Started

### 1) Requirements
- Python 3.11+ recommended
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
