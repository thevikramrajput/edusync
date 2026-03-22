# PHASE 5: Notifications

## Objectives
- Configure multi-channel notification infrastructure.
- Allow role-based and system-triggered announcements.

## Features to Build
1. **Notification Agent Engine**: Routing logic prioritizing critical alerts via SMS/Push and standard ones via Email/In-app.
2. FCM (Firebase Cloud Messaging) integration for Push Notifications.
3. Twilio / Fast2SMS integration for SMS.
4. Nodemailer + SendGrid for Email delivery.
5. Cron Jobs (`node-cron`) for scheduled reminders (e.g., homework due tomorrow).
6. Parent preferences panel (opt-in/out of specific channels).

## API Endpoints to Create
- `POST /api/notifications/send`
- `GET /api/notifications`
- `PUT /api/users/preferences/notifications`
- `POST /api/notifications/webhook/delivery`

## Database Migrations Needed
- `Notification` model to store in-app alerts.
- Update `User` or `ParentProfile` to store FCM tokens and contact preferences.

## Testing Checklist
- [ ] A broadcast announcement from the Admin reaches Teacher dashboards immediately.
- [ ] Fee reminders trigger an SMS to Parents successfully.
- [ ] Parent can toggle off SMS notifications and only receive Emails.
- [ ] Cron job correctly fires daily attendance summaries at 4 PM.

## Definition of Done
- Users reliably receive multi-channel notifications in real-time or on schedule, based on their individual preference settings or system criticality.
