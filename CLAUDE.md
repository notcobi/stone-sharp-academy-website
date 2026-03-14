# Stone Sharp Academy - Main Website

## What This Is
Marketing website for Stone Sharp Academy, a structured math tutoring business for Grades 9-12 in Edmonton, AB. This is the primary lead generation site - if it breaks, revenue drops to zero.

## Architecture
- **Frontend**: Static HTML/CSS/JS in `frontend/`
- **Backend**: Flask app in `backend/app.py`, served via Gunicorn
- **Deployment**: Dockerized, deployed on Railway
- **Database**: PostgreSQL (via `DATABASE_URL` env var)
- **Email**: Resend API sends lead notifications to `torsten@stonesharp.academy`

## Critical Data Pathway
```
contact.html form (#quoteForm)
  → frontend/js/main.js initQuoteForm() → fetch('/submit', FormData)
  → backend/app.py /submit route
  → Saves lead to PostgreSQL (leads table)
  → Sends email notification via Resend
```
**Form fields**: `name`, `email`, `phone`, `grade`, `message`

This is the only revenue-generating pathway on the site. Protect it at all costs.

## Repo Situation
- **This repo** (notcobi/stone-sharp-academy-website): Alex's deploy repo, connected to Railway
- **Torsten's repo** (Torstoner/MainWebsite): Added as `upstream` remote. Torsten makes design/marketing changes here
- Torsten is the founder/marketing person, not technical. His changes may inadvertently break backend wiring (e.g., replacing fetch() calls with localStorage stubs)
- Always diff carefully when merging upstream changes. Design is safe; data pathways need line-by-line review.

## Key Files
- `backend/app.py` - Flask server, form handler, Resend email, DB writes
- `frontend/js/main.js` (or `app.js`) - Client-side form submission, nav, UI interactions
- `frontend/contact.html` - Contact form (the lead gen form)
- `frontend/book.html` - Booking page (Calendly embed)
- `Dockerfile` - Production container
- `backend/requirements.txt` - Python deps

## Environment Variables (Railway)
- `DATABASE_URL` - PostgreSQL connection string
- `RESEND_API_KEY` - Resend email API key
- `EMAIL_FROM` - Sender address (default: noreply@stonesharpacademy.com)
- `PORT` - Server port

## Rules
- Never deploy without verifying the contact form submission pathway works end-to-end
- When merging Torsten's changes: take design, keep backend wiring
- The `initQuoteForm()` function in main.js is sacred - it must always use `fetch('/submit')`, never localStorage
