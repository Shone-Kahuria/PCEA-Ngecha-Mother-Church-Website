# PCEA Ngecha Mother Church Website

This repository now contains a full v1 implementation of the PCEA Ngecha website platform based on the requirements specification.

## What Is Implemented

- App factory pattern with environment-based configuration
- Core Flask extensions (SQLAlchemy, Migrate, Login, Mail, CSRF)
- Full schema for leadership, districts, members, groups, sermons, events, announcements, gallery, donations, and communication records
- Public routes and templates for all key pages:
   - Home, About, Our Team
   - Sermons and sermon detail
   - Events and event detail
   - Districts and district detail
   - Groups and group detail
   - Gallery, Give, Contact, Prayer, Announcements
- Public form handling:
   - Contact submissions
   - Prayer requests
   - Newsletter subscriptions
- Admin dashboard with role-aware route protection and live stats
- Admin CRUD modules:
   - Districts
   - Elders
   - Ministers
   - Deacons
   - Members
   - Groups
   - Group officers
   - Sermons
   - Events
   - Announcements
- Admin operational lists:
   - Deacons
   - Groups and group officers
   - Members
   - Donations
   - Gallery overview
   - Newsletter subscribers
   - Prayer requests
   - Contact messages
   - Settings page scaffold
- JSON API endpoints:
   - /api/health
   - /api/sermons
   - /api/events
   - /api/announcements
   - /api/districts
- CLI utility commands:
   - flask init-db
   - flask seed

## Quick Start

1. Create a virtual environment:

   `python -m venv .venv`

2. Activate it (PowerShell):

   `.\.venv\Scripts\Activate.ps1`

3. Install dependencies:

   `pip install -r requirements.txt`

4. Copy environment template and edit values:

   `Copy-Item .env.example .env`

5. Run database initialization (after setting DATABASE_URL):

   `flask --app run.py init-db`

6. Seed default data (13 districts, 12 groups, admin user):

   `flask --app run.py seed`

   Optional custom admin credentials:

   `flask --app run.py seed --admin-email admin@pceangecha.co.ke --admin-password ChangeMe123!`

7. Start the app:

   `python run.py`

8. Run tests:

   `python -m pytest -q`

## Suggested Next Targets

- Add CSV export for donations and prayer requests
- Add image upload workflow for gallery and leadership profiles
- Add admin CRUD for deacons and members
- Add RSVP flow for events
- Add deployment configuration for production environment
