# PHASE 1: Foundation

## Objectives
- Establish the core project repository and infrastructure.
- Set up role-based authentication using NextAuth.js.
- Implement the primary database schema utilizing PostgreSQL and Prisma.
- Create role-specific routing on the frontend.
- Configure Docker for scalable deployment.

## Features to Build
1. Mono-repo/multi-repo structure setup.
2. Next.js App Router initialization with TailwindCSS and ShadCN UI.
3. Express + Node.js backend initialization.
4. NextAuth integration (JWT) supporting Admin, Principal, Teacher, Student, and Parent roles.
5. Role-based Protected Routes in Next.js.
6. Base UI Shell layout (Sidebar, Navbar, User Menu).

## API Endpoints to Create
- `POST /api/auth/login` (Via NextAuth Credentials provider or Backend API)
- `GET /api/users/me` - Fetch current user profile
- `GET /api/health` - System health check

## Database Migrations Needed
- Initial migration creating User, Profiles (Teacher, Student, Parent), Class, Subject, and Enums.

## Testing Checklist
- [ ] Database connects successfully via Prisma.
- [ ] Users can login with valid credentials (Admin, Teacher, Student).
- [ ] Unauthorized users are redirected to `/login`.
- [ ] Role boundaries are respected (e.g., Teachers cannot access Admin routes).
- [ ] Docker-compose starts DB, Redis, Backend, Frontend properly.

## Definition of Done
- Complete folder structure initialized.
- Next.js and Express servers run and communicate.
- Successful authentication flow across all role types.
