# Contributing to EduSync

Thank you for your interest in contributing to EduSync! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/edusync.git
   cd edusync
   ```

2. **Backend setup (Docker)**
   ```bash
   cp backend/.env.example backend/.env
   docker compose up -d
   ```

3. **Frontend setup**
   ```bash
   cd frontend
   cp .env.example .env
   npm install
   npm run dev
   ```

## Architecture Rules

All contributions **must** follow these architectural patterns:

| Rule | Description |
|------|-------------|
| **Service layer** | All writes go through service functions in `<app>/services.py` |
| **Atomic transactions** | Every write service uses `@transaction.atomic` |
| **Audit logging** | Every mutation calls `audit_log()` or `audit_bulk_create()` |
| **Branch isolation** | All branch-scoped ViewSets inherit `BaseBranchScopedViewSet` |
| **Soft delete** | Never use `queryset.delete()` — use `instance.delete()` (soft) |
| **Row locking** | Use `select_for_update()` for concurrent write operations |

## Code Style

- **Python**: Follow PEP 8. Use type hints where practical.
- **JavaScript**: Use ES6+ syntax. Prefer functional components.
- **Commits**: Use conventional commits (`feat:`, `fix:`, `docs:`, `test:`).

## Pull Request Process

1. Create a feature branch from `main`
2. Write tests for new functionality
3. Ensure all tests pass: `docker compose exec web python manage.py test --verbosity=2`
4. Update documentation if needed
5. Submit a PR with a clear description

## Testing

```bash
# Run all tests
docker compose exec web python manage.py test --verbosity=2

# Run specific app tests
docker compose exec web python manage.py test accounts.tests -v2
docker compose exec web python manage.py test exams.tests -v2
docker compose exec web python manage.py test assessments.tests -v2

# Performance tests (takes ~10s, seeds 5000 students)
docker compose exec web python manage.py test core.tests_performance -v2
```

## Questions?

Open an issue on GitHub or reach out to the maintainer.
