# PHASE 2: Data Engine

## Objectives
- Build robust data ingestion pipelines for Excel/CSV/PDF.
- Implement data parsing and validation utilizing SheetJS.
- Develop the "Report Intelligence Agent" utilizing LLMs for data mapping and cleaning.

## Features to Build
1. Drag-and-drop Excel/CSV upload UI with progress tracking.
2. SheetJS parsing on the backend to extract raw data.
3. Schema-matching algorithm to map varied columns to DB models (Attendance, Marks, Fees).
4. Unstructured data cleaning utility (detect empty rows, remove duplicates).
5. Conflict resolution UI (Admin interface to manually correct flagged rows).
6. Auto-generation of refined Excel + PDF reports from the ingested data.

## API Endpoints to Create
- `POST /api/data/upload` - Accepts multipart form data.
- `POST /api/agents/report-intel/process` - Queues a BullMQ job for data refinement.
- `GET /api/data/jobs/:id` - Polls status of data processing.
- `GET /api/reports/download/:type` - Downloads Excel/PDF output.

## Database Migrations Needed
- Dedicated tables/models for tracking `DataUploadJob` and `ConflictLog`.

## Testing Checklist
- [ ] Uploading a standard 500-row Excel file parses in under 5 seconds.
- [ ] Malformed columns (e.g., 'stdnt_name' instead of 'Student Name') are correctly matched by the AI agent.
- [ ] Duplicate entries are flagged for review instead of crashing the DB.
- [ ] Re-exporting processed data matches the verified DB state.
- [ ] Background queue handles concurrent uploads gracefully.

## Definition of Done
- Admin can upload a messy Excel file, the AI Agent cleans it, maps it to the DB schemas, and outputs a pristine PDF/Excel summary report.
