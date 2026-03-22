# PHASE 6: Polish + Production

## Objectives
- Optimize for performance and scalability.
- Prepare the Next.js app as a Progressive Web App (PWA).
- Audit security and finalize deployment pipelines.

## Features to Build
1. **PWA Setup**: `next-pwa` integration, Service Workers, offline fallback page, install prompts.
2. **Performance Improvements**: Redis caching for heavy queries, DB indexing, image optimization.
3. **Security Audit**: Comprehensive rate limiting, Helmet for HTTP headers, Prisma parameterized queries verifications.
4. **Local LLM Migration Plan**: Configuration toggles to switch `AI_PROVIDER` to a custom Ollama endpoint.
5. **Deployment Scripts**: Finalizing Docker environments, GitHub Actions CI/CD pipelines.

## API Endpoints to Create
- Configuration/Environment introspections (Admin only).

## Database Migrations Needed
- Refinement: adding compound indexes on highly queried fields (e.g., `Attendance(date, classId)`).

## Testing Checklist
- [ ] App is installable on mobile devices (A2HS).
- [ ] Lighthouse score for performance, accessibility, and SEO is 90+.
- [ ] Switching `AI_PROVIDER=Ollama` correctly routes requests to the local inference API.
- [ ] Rate limiting rejects >100 requests/min from a single IP.

## Definition of Done
- The RED School EduOS is secure, highly performant, accessible offline, and fully deployed to output production environments with CI/CD enabled.
