# RED School EduOS

A production-ready, multi-agent SaaS platform for R.E.D. School, Jhajjar, Haryana.

## Project Structure

```text
red-school-eduos/
├── phases/                   # Phase documentation (PHASE_1.md to PHASE_6.md)
├── frontend/                 # Next.js 14 Frontend App (PWA)
│   ├── src/
│   │   ├── app/              # App Router (Pages, Layouts)
│   │   ├── components/       # Shared UI components (ShadCN, custom)
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # Utility functions, API clients
│   │   ├── store/            # State management
│   │   └── types/            # TypeScript interfaces
│   ├── public/               # Static assets, PWA manifest
│   ├── package.json
│   └── next.config.js
├── backend/                  # Express.js + Node.js Backend API
│   ├── src/
│   │   ├── controllers/      # Route handlers
│   │   ├── middlewares/      # Auth, Error handling, Rate limiting
│   │   ├── routes/           # Express routes definitions
│   │   ├── services/         # Business logic
│   │   ├── workers/          # BullMQ background workers
│   │   └── utils/            # Helper functions, logger
│   ├── prisma/
│   │   ├── schema.prisma     # Database schema
│   │   └── migrations/       # DB migration history
│   ├── package.json
│   └── tsconfig.json
├── docker-compose.yml        # Multi-container orchestration
├── project_todo.md           # Notion synced task list
├── PATENT_NOTES.md           # Provisional patent documentation
└── README.md                 # Project overview
```
