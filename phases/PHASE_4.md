# PHASE 4: AI Agents

## Objectives
- Integrate specialized AI agents utilizing OpenAI GPT-4o.
- Handle prompt engineering, API calls, error handling, and BullMQ queue management.

## Features to Build
1. **Academic Planning Agent**: Generator for weekly/monthly lesson plans, assignments, and quizzes.
2. **Student Support Agent**: Context-aware AI Chatbot with "Explain this concept" functionality and Web Speech API.
3. **School Operations Agent**: Automated background analyzer triggering <75% attendance alerts, >30 days fee defaults, and performance drop trends.
4. **Analytics Dashboard**: Data visualization for operations (heatmaps, pass/fail rates).

## API Endpoints to Create
- `POST /api/agents/academic/plan`
- `POST /api/agents/academic/assignment`
- `POST /api/agents/support/chat`
- `GET /api/operations/analytics`

## Database Migrations Needed
- `LecturePlan` and `Assignment` tracking.
- Cache storage for chat histories (can also use Redis).

## Testing Checklist
- [ ] Academic agent generates a CBSE-aligned 10th-grade Math lesson plan in < 15 seconds.
- [ ] Student chatbot correctly references the student's previous marks when giving advice.
- [ ] Operations agent correctly identifies and flags students below 75% attendance.
- [ ] All LLM calls have 3 retries with exponential backoff on failure.

## Definition of Done
- The 3 advanced AI agents (Planning, Tutoring, Operations) are active, stable, and providing accurate, context-aware responses to users.
