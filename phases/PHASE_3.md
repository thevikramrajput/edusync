# PHASE 3: School Core

## Objectives
- Provide comprehensive modules for daily school operations.
- Implement Attendance marking, Result publishing, Fee tracking, and Timetables.

## Features to Build
1. **Attendance Module**: Daily subject/class-wise attendance, calendar view, bulk mark.
2. **Marks & Results**: Entry form for unit tests/terms, CBSE grade calculation (A1-E).
3. **Fee Management**: Track dues, record partial/full payments, generate PDF receipts.
4. **Timetable Builder**: Drag-and-drop UI for associating teachers with periods, conflict warnings.

## API Endpoints to Create
- `GET/POST /api/attendance`
- `GET/POST /api/marks`
- `GET/POST /api/fees`
- `GET/POST /api/timetables`

## Database Migrations Needed
- Introduce `Timetable` and `Period` models. 
- Expand `Fee` structures if payment gateway tracking is added.

## Testing Checklist
- [ ] Teacher can mark attendance for their assigned class and view the calendar.
- [ ] Entering marks auto-calculates correct CBSE grades.
- [ ] Fee receipts export accurately to PDF.
- [ ] Assigning a teacher to two overlapping periods triggers a conflict error.

## Definition of Done
- All basic school administrative operations (Attendance, Marks, Fees, Timetable) are functional via the Admin/Teacher dashboards.
