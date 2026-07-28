# CineVerseX

CineVerseX is a Flask-based movie discovery and ticket-booking platform with a public catalog, theater/show management, seat booking, UPI-style payments, user tickets, wishlist tools, reporting, analytics, and a full admin workspace.

Live demo: https://cineversex.onrender.com

## What It Does

- Browse movies, search the catalog, view details, read/write reviews, and save movies to a wishlist.
- Discover IMDb-backed movie data with packaged seed data and generated poster fallbacks.
- Manage theaters, screens, shows, movies, users, reviews, system settings, and activity logs from admin views.
- Book seats for shows, view booking history, cancel tickets, download ticket PDFs, and track payments/refunds.
- Explore revenue charts, advanced analytics, CSV reports, trending/upcoming API endpoints, and health checks.
- Support account registration, login, Google OAuth, password reset, email verification, profiles, and plan/subscription flows.
- Run locally with SQLite by default, or use PostgreSQL with Flask-Migrate/Alembic for production-style deployments.

## Tech Stack

| Layer | Tools |
| --- | --- |
| Backend | Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate |
| Database | SQLite for local fallback, PostgreSQL for production |
| Auth | Password auth, Flask-Login, Google OAuth |
| Email | Flask-Mail |
| UI | Jinja templates, Bootstrap, custom CSS, light/dark theme script |
| Tickets & Reports | QR code generation, PDF generation, CSV exports |
| Deployment | Gunicorn, Render-compatible config |

## Project Structure

```text
CineVerseX/
  backend/
    app.py                 # Flask app, extensions, blueprints, request hooks
    config.py              # Environment-driven app/database config
    auth/                  # Role/access guards
    data/                  # Packaged IMDb seed database
    models/                # SQLAlchemy models
    routes/                # Flask blueprints
    services/              # Business logic, startup seed, reports, security
    static/                # CSS, JS, images
    templates/             # Jinja pages
  migrations/              # Flask-Migrate/Alembic migrations
  scripts/                 # Data preparation helpers
  migrate_sqlite_to_postgres.py
  requirements.txt
  vercel.json
  README.md
```

## Quick Start

1. Clone the repository.

```bash
git clone https://github.com/chevior/CineVerseX.git
cd CineVerseX
```

2. Create and activate a virtual environment.

```bash
python -m venv venv
venv\Scripts\activate
```

For Linux or macOS:

```bash
source venv/bin/activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Create your environment file.

```bash
copy .env.example .env
```

For Linux or macOS:

```bash
cp .env.example .env
```

5. Start the app.

```bash
python backend/app.py
```

Open http://127.0.0.1:5000.

On first startup, CineVerseX creates the database tables, default settings, a development admin user, sample theater data, and curated movie data unless the related seed flags are disabled.

## Environment Variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | Recommended | Flask session/signing secret. Use a strong value outside local development. |
| `DATABASE_URL` | No | SQLAlchemy database URL. If omitted or left as the placeholder, the app uses `backend/cineversex.db`. |
| `GOOGLE_CLIENT_ID` | No | Enables Google OAuth login when paired with the secret. |
| `GOOGLE_CLIENT_SECRET` | No | Google OAuth client secret. |
| `GOOGLE_REDIRECT_URI` | No | OAuth callback URL, usually `http://127.0.0.1:5000/auth/google/callback` locally. |
| `MAIL_SERVER` | No | SMTP host for verification and password reset email. |
| `MAIL_PORT` | No | SMTP port. Defaults to `587`. |
| `MAIL_USE_TLS` | No | Whether SMTP should use TLS. Defaults to `true`. |
| `MAIL_USERNAME` | No | SMTP username. |
| `MAIL_PASSWORD` | No | SMTP password or app password. |
| `MAIL_DEFAULT_SENDER` | No | Sender address for app email. |
| `SKIP_STARTUP_INIT` | No | Set to `1`, `true`, or `yes` to skip startup initialization. |
| `SKIP_CURATED_CATALOG_SEED` | No | Set to `1`, `true`, or `yes` to skip curated catalog seeding. |
| `ENABLE_STARTUP_CATALOG_SYNC` | No | Set to `1`, `true`, or `yes` to attempt external catalog sync on startup. |
| `IMDB_DB_PATH` | No | Optional custom path for IMDb seed data. |

## Database Workflow

For local development, you can rely on the automatic SQLite fallback:

```bash
python backend/app.py
```

For PostgreSQL, set `DATABASE_URL` and apply migrations:

```bash
flask --app backend.app db upgrade
```

To migrate existing local SQLite data into PostgreSQL:

```bash
python migrate_sqlite_to_postgres.py --sqlite-path backend/cineversex.db --postgres-url postgresql://user:password@localhost:5432/cineversex
```

The migration helper can also build the PostgreSQL URL from `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, and `PGPASSWORD`.

## Development Admin

Startup initialization creates or refreshes this local admin account:

```text
Email: nchethan066@gmail.com
Password: admin123
```

Change or remove these credentials before deploying anywhere public.

## Useful Routes

| Route | Description |
| --- | --- |
| `/` | Home page |
| `/movies` | Movie catalog |
| `/search` | Movie search |
| `/theaters` | Theater listing |
| `/shows` | Show listing |
| `/wishlist` | User wishlist |
| `/booking-history` | User booking history |
| `/my-tickets` | User tickets |
| `/payments/pricing` | Subscription/pricing page |
| `/admin/dashboard` | Admin dashboard |
| `/admin/reports` | CSV/reporting hub |
| `/api/movies` | Movies API |
| `/api/trending` | Trending API |
| `/api/upcoming` | Upcoming API |
| `/health` | Health check |

## Deployment Notes

- Use PostgreSQL for deployed environments.
- Set a strong `SECRET_KEY`.
- Configure Google OAuth redirect URLs for the deployed domain.
- Configure SMTP credentials if email verification or password resets should send mail.
- Disable or customize default development credentials before launch.
- Run migrations as part of release setup:

```bash
flask --app backend.app db upgrade
```

- Start with Gunicorn:

```bash
gunicorn backend.app:app
```

## Author

Built by Chethan N. (`chevior`)

GitHub: https://github.com/chevior

## License

This project is developed for educational and portfolio purposes.
