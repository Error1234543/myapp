# AURA SPACE

AURA SPACE is a calm, mobile-first personal workspace for everyday planning and digital organization.

## Current features
- Overview dashboard
- Task manager with due dates, completion filters and deletion
- Notes with create, edit and search
- Monthly calendar with task markers
- Smart tools: text helper, focus timer and quick thought capture
- Responsive mobile navigation and light/dark appearance
- Local-first storage using browser localStorage

## Project layout
- `frontend/` — static AURA SPACE app (HTML, CSS, JavaScript).
- `backend/` — existing FastAPI service retained for future integrations.
- `Dockerfile` — retained from the previous backend deployment setup.

## Vercel deployment
Set Root Directory to `frontend`, Framework Preset to `Other`, and leave Build Command and Output Directory empty/default. This is a plain HTML/CSS/JS app and needs no build step.

## Data and privacy
Tasks, notes, profile label and appearance preference are stored in this browser on this device. They do not sync across devices yet. Cloud sync and account authentication require a future backend/database integration. Do not store sensitive information in this prototype.
