<p align="center">
  <h1 align="center">📚 EduSync</h1>
  <p align="center">
    <strong>Multi-Branch School Management SaaS</strong><br>
    Enterprise-grade backend + admin frontend for managing students, exams, assessments, and academic operations across multiple school branches.
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Django-5.x-green?logo=django" alt="Django">
  <img src="https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/React-19-blue?logo=react" alt="React">
  <img src="https://img.shields.io/badge/Docker-Compose-blue?logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/Tests-55%20passing-brightgreen" alt="Tests">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

---

## Overview

EduSync is a production-grade, multi-branch school ERP system designed for SaaS deployment. It enforces strict **branch-level data isolation**, uses **service-layer architecture** with atomic transactions, and includes a **comprehensive audit trail** for every data mutation.

Built for 3 initial branches (CHK, JJR, DADRI) with architecture ready for multi-tenant SaaS expansion.

---

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   React SPA  │────▶│  Django DRF  │────▶│  PostgreSQL 16   │
│  (Vite 7.x)  │     │   API v1     │     │  Branch-Scoped   │
│  Port: 3000  │     │  Port: 8000  │     │  Partial Indexes │
└──────────────┘     └──────┬───────┘     └──────────────────┘
                            │
                     ┌──────┴───────┐
                     │ Service Layer│
                     │  @atomic     │
                     │  audit_log() │
                     │  row locking │
                     └──────────────┘
```

### Key Architectural Patterns

| Pattern | Implementation |
|---------|---------------|
| **Service Layer** | All writes go through `<app>/services.py` with `@transaction.atomic` |
| **Branch Isolation** | `BaseBranchScopedViewSet` auto-filters by user's branch; `BranchScopedManager` enforces at ORM level |
| **Audit Logging** | Every CREATE/UPDATE/DELETE logged via `audit_log()` with old→new diffs |
| **Row-Level Locking** | `select_for_update()` prevents concurrent overwrites on exam marks |
| **Soft Delete** | `BaseModel.delete()` sets `is_deleted=True`; partial unique constraints allow re-creation |
| **Partial Unique Constraints** | Unique constraints only apply to non-deleted records |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 5.x, Django REST Framework |
| **Auth** | JWT (SimpleJWT) with token blacklisting |
| **Database** | PostgreSQL 16 with partial indexes |
| **Frontend** | React 19, Vite 7, React Router 7 |
| **HTTP Client** | Axios with JWT interceptor + auto-refresh |
| **Containerization** | Docker Compose |
| **Static Files** | WhiteNoise |
| **API Docs** | drf-spectacular (OpenAPI 3.0 / Swagger) |
| **Deployment** | Railway (backend) + Vercel (frontend) |

---

## Features

### Backend
- ✅ **40+ models** across 12 Django apps
- ✅ **JWT authentication** with login, refresh, logout, and `/me/` endpoint
- ✅ **Student CRUD** with branch-scoped isolation
- ✅ **Exam engine** — types, exams, bulk marks submission, report cards with grade mapping
- ✅ **Assessment engine** — criteria scoring, DRAFT→SUBMITTED→APPROVED workflow
- ✅ **Request logging middleware** — method, path, user_id, branch_id, response_time_ms
- ✅ **Health probes** — readiness (`/health/`) + liveness (`/health/live/`)
- ✅ **Seeder command** — idempotent `seed_initial_data` for branches, roles, assessment types

### Frontend
- ✅ Login page with JWT auth
- ✅ Protected routes with auto-redirect
- ✅ Sidebar navigation layout
- ✅ Student list (paginated, searchable)
- ✅ Student detail page
- ✅ Exam marks bulk entry + submission
- ✅ Report card (totals, percentage, grade)
- ✅ Assessment entry with criteria scores, submit, approve

### Security
- 🔒 HTTPS enforcement (HSTS 1 year, preload)
- 🔒 Secure cookies (HttpOnly, SameSite, Secure)
- 🔒 PBKDF2 / Argon2 / BCrypt password hashers
- 🔒 Rate limiting (anon: 10/min, user: 60/min in production)
- 🔒 Branch-level data isolation at ORM + ViewSet level
- 🔒 Obscured admin URL

---

## Test Suite — 55 Tests Passing

```
Ran 55 tests in 30.2s — OK ✅
```

| Category | Tests |
|----------|-------|
| Soft delete behavior | 4 |
| Branch isolation | 4 |
| Audit logging | 3 |
| User model validation | 3 |
| Unique constraints | 4 |
| Service layer atomicity | 3 |
| API integration (JWT, CRUD, bulk) | 12 |
| Row locking | 1 |
| Seeder idempotency | 1 |
| AcademicYear enforcement | 1 |
| Status transitions (assessments) | 6 |
| Score validation + rollback | 3 |
| **Performance baseline** | **5** |

### Performance Baseline

Seeded **5,000 students** and **30,000 exam marks**:

| Metric | Target | Result |
|--------|--------|--------|
| Report card query | < 500ms | ✅ Pass |
| Branch-filtered list | < 200ms | ✅ Pass |
| N+1 query detection | ≤ 4 queries | ✅ Pass |

---

## Quick Start (Docker)

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend)

### 1. Clone & Configure

```bash
git clone https://github.com/your-username/edusync.git
cd edusync
cp backend/.env.example backend/.env
# Edit backend/.env with your values
```

### 2. Start Backend

```bash
docker compose up -d
# Waits for DB → runs migrations → seeds data → starts Gunicorn
```

### 3. Start Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
# → http://localhost:3000
```

### 4. Create Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

### 5. Verify

```bash
# Health check
curl http://localhost:8000/api/v1/health/

# API docs
open http://localhost:8000/api/docs/

# Run tests
docker compose exec web python manage.py test --verbosity=2
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login/` | JWT login |
| POST | `/api/v1/auth/refresh/` | Refresh access token |
| POST | `/api/v1/auth/logout/` | Blacklist refresh token |
| GET | `/api/v1/auth/me/` | Current user profile |
| CRUD | `/api/v1/auth/students/` | Student management |
| CRUD | `/api/v1/exams/types/` | Exam types |
| CRUD | `/api/v1/exams/list/` | Exams |
| CRUD | `/api/v1/exams/marks/` | Exam marks |
| POST | `/api/v1/exams/marks/bulk/` | Bulk marks submission |
| GET | `/api/v1/exams/marks/report-card/` | Report card |
| CRUD | `/api/v1/assessments/types/` | Assessment types |
| CRUD | `/api/v1/assessments/student/` | Student assessments |
| POST | `/api/v1/assessments/student/{id}/submit/` | Submit assessment |
| POST | `/api/v1/assessments/student/{id}/approve/` | Approve assessment |
| GET | `/api/v1/assessments/student/quarterly-summary/` | Quarterly summary |
| GET | `/api/v1/health/` | Readiness probe |
| GET | `/api/v1/health/live/` | Liveness probe |
| GET | `/api/docs/` | Swagger UI |

---

## Deployment

### Backend → Railway

1. Create Railway project with PostgreSQL plugin
2. Connect GitHub repo → set root directory to `backend/`
3. Set env vars (see `backend/.env.production`)
4. Railway auto-detects `Procfile` and runs migrations + seeds

### Frontend → Vercel

1. Connect GitHub repo → set root directory to `frontend/`
2. Set `VITE_API_BASE_URL` to your Railway backend URL
3. Deploy — Vercel uses `vercel.json` for SPA routing

---

## Project Structure

```
edusync/
├── backend/
│   ├── accounts/          # User model, auth, students
│   ├── academics/         # Classes, sections, subjects
│   ├── assessments/       # Assessment engine + scoring
│   ├── audit/             # Audit log model
│   ├── common/            # BaseModel, managers, middleware, services
│   ├── core/              # School, Branch, Quarter, GradeMapping
│   ├── exams/             # Exam engine + marks + report cards
│   ├── edusync/settings/  # base / development / production
│   ├── Dockerfile
│   ├── Procfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api.js         # Axios + JWT interceptor
│   │   ├── context/       # AuthContext
│   │   ├── components/    # Layout, ProtectedRoute
│   │   └── pages/         # Login, Students, Exams, etc.
│   └── vercel.json
├── docker-compose.yml
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

---

## License

MIT — see [LICENSE](LICENSE).
