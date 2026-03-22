# RED School EduOS - Project Tasks

## Must Have (MVP)
| Feature | Description | Phase | Priority | Effort |
|---------|-------------|-------|----------|--------|
| Auth System | JWT based role-based access for Admin, Principal, Teacher, Student, Parent | 1 | P0 | M |
| Dashboard | Role-specific views with basic stat cards | 1 | P0 | M |
| DB Schema & Setup | PostgreSQL setup with Prisma ORM models for all core entities | 1 | P0 | S |
| Excel Upload & Parse | Upload xlsx/csv, format validation, SheetJS integration | 2 | P0 | L |
| Report Generation | Report Intelligence Agent (Attendance/Marks/Fees -> Excel/PDF) | 2 | P0 | L |
| Attendance Module | Mark daily attendance, calendar view | 3 | P0 | M |
| Marks & Results | Enter marks, auto-grade CBSE scale, basic reports | 3 | P0 | M |
| Fee Management | Setup structure, track payments, basic receipts | 3 | P0 | M |
| Timetable builder | Visual timetable builder, conflict detection | 3 | P0 | L |

## Should Have
| Feature | Description | Phase | Priority | Effort |
|---------|-------------|-------|----------|--------|
| Academic Planning Agent | AI-powered lesson plans, assignments, quizzes generator | 4 | P1 | L |
| Operations Agent Alerts | Automated attendance (<75%), fee (>30d), performance alerts | 4 | P1 | M |
| Notification System | FCM push, Email, SMS delivery with node-cron | 5 | P1 | L |
| Chatbot (Student) | GPT-4o tutor chatbot with context of student's subjects | 4 | P1 | L |

## Nice to Have
| Feature | Description | Phase | Priority | Effort |
|---------|-------------|-------|----------|--------|
| Voice Input | Web Speech API for chatbot | 4 | P2 | S |
| Operations Analytics | School analytics dashboard (heat maps, trends) | 4 | P2 | M |
| Notification Prefs | User-configurable notification channels | 5 | P2 | S |
| PWA Setup | Offline support, installable mobile view | 6 | P2 | M |
| Local LLM Migration | Structure platform to swap GPT-4 for local Ollama models later | 6 | P2 | L |
