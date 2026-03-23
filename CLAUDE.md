# CLAUDE.md — Online Hostel Information Management System
## Architectural Memory Document | Living Reference | Single Source of Truth

> **Purpose**: This file is the permanent architectural memory for this project.
> It must be read at the start of every session and updated after every significant change.
> Do NOT modify application code without consulting this document first.

---

## 1. PROJECT PURPOSE & SCOPE

This is a **Django-based Online Hostel Information Management System** for a university/institution context.

The system manages:
- Student accommodation records (who lives where)
- Hostel / Block / Room inventory
- Room allocation (admin assigns students to rooms)
- Payment tracking (students submit payment records, admins verify them)
- Administrative reports (occupancy, allocations, payments)

**NOT in scope**: Automatic allocation algorithms, email gateways, payment gateways, REST APIs, mobile apps.

**Context**: Appears to be a Ugandan institution (Africa/Kampala timezone implied by UGX currency conventions; TIME_ZONE is incorrectly set to UTC).

---

## 2. CORE DOMAIN CONCEPTS

| Domain Term      | Django Model        | Meaning |
|------------------|---------------------|---------|
| Hostel           | `Hostel`            | A hall of residence (e.g., "Block A Male Hostel") |
| Block            | `Block`             | A wing or section within a hostel |
| Room             | `Room`              | An individual room with a bed capacity |
| Resident/Student | `CustomUser`        | A student occupying (or seeking) a room |
| Manager/Warden   | `CustomUser`        | A staff member who administers the hostel |
| Allocation       | `Allocation`        | The link between a student and a room for a period |
| Payment          | `Payment`           | A hostel fee payment record submitted by a student |
| Academic Year    | CharField on models | e.g., "2024/2025" — used to segment allocations/payments |

---

## 3. HIGH-LEVEL SYSTEM ARCHITECTURE

```
hostel_system/                   ← Django project root
├── hostel_system/               ← Project config package
│   ├── settings.py              ← Settings (see known issues)
│   └── urls.py                  ← Root URL conf
├── users/                       ← Auth, registration, dashboards
├── hostels/                     ← Hostel/Block/Room inventory
├── allocations/                 ← Room allocation logic
├── payments/                    ← Payment records & verification
├── reports/                     ← Read-only report views + CSV export
├── templates/                   ← Global template directory
│   ├── base.html                ← Master layout (Bootstrap 5)
│   ├── navbar.html              ← Navigation (role-aware)
│   ├── users/                   ← Login, register, dashboards
│   ├── allocations/             ← Allocation list, create, rooms
│   ├── payments/                ← Payment list, create, verify
│   └── reports/                 ← Report templates
└── static/                      ← Static files directory (empty)
```

**Frontend**: Bootstrap 5.3 CDN + Bootstrap Icons. No JavaScript framework. All server-side rendering.

**Database**: SQLite (`db.sqlite3`). Sufficient for development; needs PostgreSQL for production.

**Auth**: Django's built-in session auth. Custom user model: `users.CustomUser`.

---

## 4. INSTALLED APPS & RESPONSIBILITIES

| App           | URL Prefix     | Responsibility |
|---------------|----------------|----------------|
| `users`       | `/`            | Auth (login/logout/register), dashboards, user profiles |
| `hostels`     | *(none)*       | Hostel/Block/Room models — **admin-only management**, no web UI views |
| `allocations` | `/allocations/`| List & create allocations; available rooms view |
| `payments`    | `/payments/`   | Student payment submission; admin verification |
| `reports`     | `/reports/`    | Read-only HTML reports + CSV export |

> **Important**: The `hostels` app has NO web-facing views or URLs. Hostel/Block/Room data is managed **exclusively through Django Admin**. This is a significant gap.

---

## 5. CORE MODELS & REAL-WORLD MEANING

### 5.1 CustomUser (`users/models.py`)
Extends Django's `AbstractUser`. Adds:
- `is_student` (BooleanField) — True for student accounts
- `is_manager` (BooleanField) — True for hostel manager/warden accounts
- `student_id` (unique, nullable) — Institution student number
- `department`, `level` — Academic classification
- `phone_number`, `date_of_birth`, `gender`

**Role determination** (current logic):
```python
# "Admin" check used in ALL protected views and navbar:
request.user.is_manager or request.user.is_staff
```

### 5.2 Hostel → Block → Room (`hostels/models.py`)
Three-level physical hierarchy:
```
Hostel (e.g., "Makerere Female Hostel")
  └── Block (e.g., "Wing A")
       └── Room (e.g., "Room 101", capacity=4)
```
- `Hostel.gender`: Male / Female / Mixed
- `Block.capacity`: Manually entered integer — **does not auto-sync with room capacities**
- `Room.capacity`: Number of beds
- `Room.is_full`: Boolean, cached/derived — maintained via `check_and_update_full_status()`

### 5.3 Allocation (`allocations/models.py`)
Links a student to a room.
- `status`: active | left | cancelled
- `date_allocated`: auto-set on creation
- `date_left`: set when student leaves (nullable)
- `academic_year`: e.g., "2024/2025"
- Validation prevents: (a) over-capacity rooms, (b) dual active allocations per student
- Validation is in `clean()` called from `save()` — **not enforced at DB level**

### 5.4 Payment (`payments/models.py`)
Student-submitted payment record awaiting admin verification.
- `status`: pending | verified | rejected
- `reference_number`: Bank/mobile money transaction ID (unique)
- `verified_by`: FK to the admin who verified it
- `date_verified`: set on verification

### 5.5 Car (`payments/models.py`) ⚠️ FOREIGN OBJECT
A `Car` model (make, model, name, price) exists in the `payments` app. It has a migration (`0002_car.py`) and is registered in `PaymentAdmin`. **This is irrelevant test/practice code accidentally committed.** It exists in the live database.

---

## 6. KEY RELATIONSHIPS & DATA OWNERSHIP

```
CustomUser (student)
  └──< Allocation >──── Room ──── Block ──── Hostel
  └──< Payment (self-submitted)

CustomUser (admin/manager)
  └── verifies Payment (Payment.verified_by)
  └── creates Allocation
```

- A student can have **at most one active allocation** at a time (enforced in clean())
- A room has a `capacity`; allocations with status='active' count against it
- A payment belongs to the student who submitted it (`payment.user = request.user` set in view)

---

## 7. AUTHENTICATION & AUTHORIZATION

### Current Approach
- **Session-based auth** (Django default)
- **Login required**: `@login_required` decorator on all non-public views
- **Role check**: Inline in every view — `if not (request.user.is_manager or request.user.is_staff)`
- **No custom permission classes or decorators** — all ad hoc

### Role Determination (current, flawed)
```python
# "admin" = is_manager OR is_staff (Django's built-in staff flag)
# This conflates two different concepts
```

### Access Control Matrix (current implementation)

| Feature                    | Student | Manager/Staff | Public |
|----------------------------|---------|---------------|--------|
| Home page                  | ✓       | ✓             | ✓      |
| Register                   | ✓       | ✓             | ✓      |
| Login                      | ✓       | ✓             | ✓      |
| Student Dashboard          | ✓       | ✓ (unguarded) | ✗      |
| Admin Dashboard            | ✗       | ✓             | ✗      |
| Create Payment             | ✓       | ✓ (unguarded) | ✗      |
| View All Payments          | ✗       | ✓             | ✗      |
| Verify Payment             | ✗       | ✓             | ✗      |
| View All Allocations       | ✗       | ✓             | ✗      |
| Create Allocation          | ✗       | ✓             | ✗      |
| Available Rooms            | ✗       | ✓             | ✗      |
| All Reports                | ✗       | ✓             | ✗      |

> ⚠️ Note: `student_dashboard` and `create_payment` have NO role guard. Any authenticated user (including managers) can access them.

---

## 8. USER ROLES & HIERARCHY

| Role         | How Set                            | Django Flags          | Notes |
|--------------|------------------------------------|-----------------------|-------|
| Superuser    | `createsuperuser` command          | `is_superuser=True`   | Has all permissions |
| Manager/Staff| Set in Django admin manually       | `is_manager=True` OR `is_staff=True` | Used interchangeably |
| Student      | Set on registration automatically  | `is_student=True`     | Self-registered |

**Problems**:
- A user can have `is_student=True` AND `is_manager=True` simultaneously
- `is_staff` (Django built-in) and `is_manager` (custom) overlap — no clear single source of truth
- No "Finance Officer" role — payment verification is done by any manager
- No "Warden" role distinct from "Admin"

---

## 9. DASHBOARD INTENT

| Dashboard         | Template                         | Current Content |
|-------------------|----------------------------------|-----------------|
| Admin Dashboard   | `users/admin_dashboard.html`     | Stats cards (students, hostels, rooms, allocations), quick actions, recent allocations, recent payments, pending payment alert |
| Student Dashboard | `users/student_dashboard.html`   | Current allocation details, profile summary, recent payments (last 5) |

---

## 10. KNOWN BUGS & ISSUES (Confirmed by Code Reading)

### CRITICAL BUGS

| # | Location | Issue | Impact |
|---|----------|-------|--------|
| B1 | `hostels/models.py:22-30` | `Hostel.total_capacity()` sums `block.capacity` but `Hostel.available_spaces()` sums `room.capacity`. These are different fields — capacity numbers will be **inconsistent and wrong**. | Reports show wrong capacity |
| B2 | `payments/models.py:41-46` | `Car` model in the payments app — foreign domain object with wrong field types (`IntegerField(max_length=...)` is invalid). Has a live migration. | DB pollution, admin confusion |
| B3 | `allocations/models.py:59-61` | `full_clean()` called in `save()` — Django admin bulk actions (queryset.update) bypass `save()`, creating inconsistent state. Also breaks admin batch operations. | Admin bulk ops silently bypass validation |
| B4 | `users/views.py:51-55` | `logout_view` uses GET request — any page can embed `<img src="/logout/">` to forcibly log out users (CSRF logout attack). | Security risk |
| B5 | `allocations/models.py` | No database-level unique constraint preventing dual active allocations. Only `clean()` prevents it — bypassed by `queryset.update()` or raw SQL. | Data integrity risk |

### STRUCTURAL ISSUES

| # | Location | Issue |
|---|----------|-------|
| S1 | `hostels/models.py:68-71` | `Room.occupied_beds()` does a DB query every time — triggers N+1 in loops (allocation list, reports, occupancy). |
| S2 | `hostels/models.py:61-62` | `Room.is_full` is derived state stored in DB. Can go out of sync (e.g., if direct DB edit occurs). Should be a `@property`. |
| S3 | `hostels/models.py:38-41` | `Block.capacity` is a manually entered field. No connection to sum of room capacities. Redundant and misleading. |
| S4 | `reports/views.py:43-45` | Payment totals computed with Python `sum()` over all records. Should use `aggregate(Sum('amount'))`. Fails at scale. |
| S5 | All views | Permission check `if not (request.user.is_manager or request.user.is_staff)` repeated 6+ times. No centralized decorator. |
| S6 | `hostels/` | No web UI for creating/editing Hostels, Blocks, Rooms. Admin-only via Django admin. Major operational gap. |
| S7 | `allocations/views.py` | No view for editing or deleting an allocation. No "vacate room" workflow. |
| S8 | All list views | No pagination. All records loaded — will fail with real data volume. |
| S9 | `payments/views.py:34-37` | `create_payment` has no guard. Managers can accidentally create payments for themselves. |
| S10 | `allocations/models.py` | No gender-matching check: a male student can be allocated to a Female hostel. |

### DJANGO ANTI-PATTERNS

| # | Location | Pattern |
|---|----------|---------|
| A1 | `hostels/models.py:68-71` | Cross-app import in model method (`from allocations.models import Allocation`) — circular dependency potential |
| A2 | `allocations/models.py:59-61` | `full_clean()` in `save()` — not Django convention; causes issues in migrations, fixtures, bulk operations |
| A3 | `navbar.html:18` | Business logic (role check) embedded in template — hard to change centrally |
| A4 | `hostel_system/settings.py:6` | `SECRET_KEY` is a hardcoded placeholder string — never safe even in development |
| A5 | All list views | Missing `select_related` / `prefetch_related` in some views (e.g., student dashboard allocation query) |

---

## 11. ARCHITECTURAL RISKS

| Risk | Severity | Description |
|------|----------|-------------|
| Race condition on allocation | HIGH | Two concurrent admin requests can both pass capacity validation and over-allocate |
| `Car` model in payments | MEDIUM | Pollutes schema, confuses future developers |
| `is_staff` / `is_manager` overlap | MEDIUM | Superusers and Django staff can access manager features without being labelled managers |
| No email verification | MEDIUM | Students register with unverified emails — no identity confirmation |
| SECRET_KEY in source | HIGH | Must be replaced with environment variable before any deployment |
| No pagination | MEDIUM | All data loads will fail at real scale |
| Derived state (`is_full`) | MEDIUM | Can desync; should be computed dynamically |

---

## 12. WHAT WORKS (Preserve These)

- Student registration → login → student dashboard flow ✓
- Admin dashboard statistics display ✓
- Room allocation creation with capacity validation (via clean()) ✓
- Payment submission by students ✓
- Payment verification by admins ✓
- CSV export in allocation and payment reports ✓
- Django Admin interface (comprehensive, well-configured) ✓
- Template inheritance (`base.html` → child templates) ✓
- Bootstrap 5 responsive UI ✓
- `select_related` used correctly in most admin views ✓
- `Allocation.delete()` correctly updates `room.is_full` ✓

---

## 13. WHAT IS PARTIALLY IMPLEMENTED

- Hostel occupancy report — works but has N+1 queries
- Role-based access — works but is ad hoc and incomplete
- Capacity calculation — works for allocation but `total_capacity()` and `available_spaces()` are inconsistent
- Academic year tracking — fields exist but no filtering or grouping in reports/views

---

## 14. WHAT MUST NOT BE CHANGED WITHOUT EXPLICIT APPROVAL

- The three-level hierarchy (Hostel → Block → Room) — it is semantically correct
- `Allocation.clean()` validation logic — it prevents over-allocation
- `Payment.reference_number` unique constraint — prevents duplicate payment records
- `AUTH_USER_MODEL = 'users.CustomUser'` — changing this requires a full migration reset
- All existing migrations — must only be modified with understanding of data risk

---

## 15. ASSUMPTIONS (Documented)

1. This is an **academic institution** hostel system, not a commercial hotel.
2. **Allocation is manual** — an admin/warden assigns rooms; students do not self-select.
3. **Payment is self-reported** — students submit proof of payment; admins verify it. No payment gateway.
4. **Single institution** — no multi-tenancy. All data belongs to one hostel complex.
5. **Academic year** is the primary temporal unit for grouping allocations and payments.
6. **Currency** appears to be local (UGX based on context) but `$` symbol is hardcoded.
7. `is_staff` and `is_manager` are treated as equivalent in this system.

---

## 16. IMPROVEMENT PLAN (Proposed, Awaiting Approval)

### MUST-DO (Critical — Bugs or Security)

| ID | Change | Reason | Risk |
|----|--------|--------|------|
| M1 | Fix `Hostel.total_capacity()` to use `room.capacity` sum, not `block.capacity` | B1 bug — wrong numbers | Low — method only change |
| M2 | Remove `Car` model + create migration to drop it | B2 — irrelevant domain object | Medium — requires migration |
| M3 | Change `logout` to POST-only | B4 — security | Low — template change needed |
| M4 | Move `SECRET_KEY` to environment variable (`.env`) | Security | Low for dev, critical for production |
| M5 | Add `@login_required` guard + role redirect to `student_dashboard` | S9 — any user can access | Low |
| M6 | Add pagination to all list views | S8 — data volume risk | Low |

### SHOULD-DO (Architecture & Quality)

| ID | Change | Reason | Risk |
|----|--------|--------|------|
| S-A | Create `@manager_required` decorator to replace inline role checks | Eliminates repetition, centralizes logic | Low |
| S-B | Replace `Room.is_full` BooleanField with `@property` + queryset annotation | Eliminates derived state | Medium — migration needed to remove field |
| S-C | Fix `Block.capacity` — make it computed or remove it | Redundant field | Medium |
| S-D | Replace Python `sum()` with `aggregate(Sum('amount'))` in payment report | Performance | Low |
| S-E | Add `UniqueConstraint` at DB level for one active allocation per student | Data integrity | Medium |
| S-F | Add gender-matching validation in `Allocation.clean()` | Domain correctness | Low |
| S-G | Add web UI for Hostel/Block/Room management (not just admin) | Major operational gap | Medium |
| S-H | Add `select_related` to student dashboard allocation query | Performance | Low |

### NICE-TO-HAVE (Enhancement)

| ID | Change | Reason | Risk |
|----|--------|--------|------|
| N1 | Add academic year filter to reports | Better data segmentation | Low |
| N2 | Add "vacate room" workflow (set allocation to 'left', set date_left) | Missing business operation | Low |
| N3 | Add profile editing for students | UX | Low |
| N4 | Change TIME_ZONE to Africa/Kampala | Correct timestamps | Low |
| N5 | Add `MEDIA_ROOT`/`MEDIA_URL` for payment receipt uploads | Evidence for verification | Medium |

---

## 17. SESSION LOG

### Session 001 — 2026-02-26
- Performed full read-only architectural audit
- Identified 5 critical bugs, 10 structural issues, 5 anti-patterns
- Created this CLAUDE.md
- No application code modified

---

## 18. NEW FILES ADDED

| File | Purpose |
|------|---------|
| `users/decorators.py` | `@manager_required` and `@student_required` decorators — use these on all protected views |

---

## 19. SESSION LOG

### Session 001 — 2026-02-26 (Read + Document)
- Performed full read-only architectural audit of all files
- Identified 5 critical bugs, 10 structural issues, 5 anti-patterns
- Created this CLAUDE.md
- No application code modified

### Session 002 — 2026-02-26 (Execution — MUST-DO + SHOULD-DO)

**Completed fixes:**

| Task | File(s) Changed | What Was Done |
|------|-----------------|---------------|
| Decorator created | `users/decorators.py` (NEW) | `@manager_required`, `@student_required` |
| Bug B1 fixed | `hostels/models.py` | `total_capacity()` now uses `room.capacity` (same as `available_spaces()`) |
| Bug B2 fixed | `payments/models.py`, `payments/admin.py`, `payments/migrations/0003_delete_car.py` (NEW) | `Car` model removed; migration run successfully |
| Bug B3 fixed | `users/views.py`, `templates/navbar.html` | Logout is now POST-only; navbar uses a form |
| M4 done | `hostel_system/settings.py` | `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` read from environment variables |
| M5 done | `users/views.py`, `payments/views.py` | `student_dashboard` and `create_payment` now guarded with `@student_required` |
| S-A done | `allocations/views.py`, `payments/views.py`, `reports/views.py`, `users/views.py` | All 7 admin views now use `@manager_required` — inline checks removed |
| M6 done | `allocations/views.py`, `payments/views.py`, `templates/allocations/allocation_list.html`, `templates/payments/payment_list.html` | Pagination added (20 per page) |
| S-D done | `reports/views.py` | Payment totals now use `aggregate(Sum())` instead of Python loops |
| S-F done | `allocations/models.py` | Gender-matching validation added to `Allocation.clean()` |

**Django system check**: 0 issues. All migrations applied cleanly.

**All improvement plan items completed in Session 004.**

---

### Session 003 — Phase 3: Full UI/UX Redesign (continued + completed)

**Date**: 2026-02-26

**What was done in this session**:
- Created `hostels/urls.py` with full URL patterns (hostel_list, hostel_create, hostel_edit, hostel_detail, block_create, room_create)
- Updated root `hostel_system/urls.py` to include `path('hostels/', include('hostels.urls'))` — closes S-G
- Created `templates/hostels/hostel_list.html` — card grid with stats, occupancy bar, gender badge
- Created `templates/hostels/hostel_detail.html` — header panel with stats, per-block room tables
- Created `templates/hostels/hostel_form.html` — create/edit hostel form
- Created `templates/hostels/block_form.html` — add block to hostel form
- Created `templates/hostels/room_form.html` — add room to block form with guidelines panel
- Redesigned `templates/payments/create_payment.html` — two-column: form + how-it-works info panel
- Redesigned `templates/payments/verify_payment.html` — two-column: detail table + action panel; handles already-processed payments
- Redesigned `templates/reports/reports_dashboard.html` — icon cards with inline export buttons and guide section
- Redesigned `templates/reports/allocation_report.html` — rich table with department/level, monospace IDs, status badges
- Redesigned `templates/reports/payment_report.html` — stat cards (total, verified, pending), rich table, UGX formatting
- Redesigned `templates/reports/hostel_occupancy_report.html` — per-hostel cards with stat pills, colour-coded progress bars, near-capacity warnings

**Django system check**: 0 issues.

**Previously completed in Phase 3 (session 003 start)**:
- `static/css/style.css` — full design system (CSS variables, sidebar, cards, badges, tables, forms, etc.)
- `templates/base.html` — sidebar layout with role-aware nav, public layout for unauthenticated
- All landing/auth templates: `home.html`, `login.html`, `register.html`
- `templates/users/admin_dashboard.html` — stat cards, Chart.js doughnut charts, quick actions, timelines
- `templates/users/student_dashboard.html` — welcome banner, allocation card, payment history
- `templates/users/profile.html` — avatar, edit form, allocation history
- `templates/allocations/allocation_list.html` — search/filter toolbar, rich table, pagination
- `templates/allocations/create_allocation.html` — two-column layout with info panel
- `templates/allocations/available_rooms.html` — per-hostel room tables with status
- `hostels/views.py`, `hostels/forms.py` — complete hostel CRUD views
- `users/views.py` — profile view, enhanced dashboards with chart data
- `users/forms.py` — ProfileEditForm
- `users/urls.py` — profile URL
- `allocations/views.py` — vacate_allocation view, search/filter in list
- `allocations/urls.py` — vacate URL

---

### Session 004 — 2026-03-07 (Improvement Plan Completion)

**Completed all remaining improvement plan items:**

| ID | Change | Files Changed |
|----|--------|---------------|
| S-B | `Room.is_full` is now a `@property` (no longer a DB field) | `hostels/models.py`, `hostels/admin.py`, `hostels/migrations/0002_*`, `allocations/forms.py`, `allocations/views.py`, `allocations/models.py` |
| S-C | `Block.capacity` is now a `@property` (sum of room capacities, no longer a DB field) | `hostels/models.py`, `hostels/forms.py`, `hostels/migrations/0002_*`, `templates/hostels/block_form.html` |
| S-E | DB-level `UniqueConstraint` added for one active allocation per student | `allocations/models.py`, `allocations/migrations/0002_*` |
| N1 | Academic year filter dropdown added to allocation and payment reports | `reports/views.py`, `templates/reports/allocation_report.html`, `templates/reports/payment_report.html` |
| N4 | TIME_ZONE changed from UTC to Africa/Kampala | `hostel_system/settings.py` |
| N5 | Payment receipt file upload added | `payments/models.py`, `payments/forms.py`, `payments/views.py`, `payments/migrations/0004_*`, `templates/payments/create_payment.html`, `templates/payments/verify_payment.html`, `hostel_system/settings.py`, `hostel_system/urls.py` |

**Django system check**: 0 issues. All migrations applied cleanly.

**Architecture notes post-session:**
- `Room.is_full` and `Block.capacity` are now computed properties — no DB sync issues possible
- Media files served from `BASE_DIR/media/` in dev mode (`MEDIA_ROOT`, `MEDIA_URL` configured)
- Payment receipts stored at `media/payment_receipts/`
- `Block.available_rooms()` now uses DB annotation (`Count` + `Q` + `F`) instead of property filter

**All improvement plan items are now complete.**

---

*This document is maintained by Claude Code. Update this file after every significant architectural change, bug fix, or new understanding.*

### Session 005 — 2026-03-16 (Full Debug & Clean Pass)

**All confirmed bugs and N+1 issues fixed:**

| Fix | File(s) | What Was Done |
|-----|---------|---------------|
| N+1 in available_rooms | `allocations/views.py` | Changed `prefetch_related('blocks__rooms')` → `prefetch_related('blocks__rooms__allocations')` |
| N+1 in student_hostels | `allocations/views.py` | Same prefetch fix for `room.occupied_beds()` calls in student hostel browse view |
| Sidebar badges missing on non-dashboard pages | `users/context_processors.py` (NEW), `hostel_system/settings.py` | Created `sidebar_counts` context processor; badge counts now available on ALL admin pages |
| Admin dashboard redundant context keys | `users/views.py` | Removed duplicate badge counts from `admin_dashboard` context |

**Django system check**: 0 issues. All migrations applied.
