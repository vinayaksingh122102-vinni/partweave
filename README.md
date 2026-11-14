# PARTWEAVE

> A dead device may contain the part that saves another.

PARTWEAVE is a full-stack component reuse and compatibility network for repair technicians, suppliers, and customers.

## Architecture

- `frontend/`: React + TypeScript + Vite single-page app. The UI uses a dependency-light CSS design system with Tailwind-like utility classes and SVG/HTML visualizations so it runs immediately after install.
- `backend/`: Flask REST API. The service uses PostgreSQL when `DATABASE_URL` is present and a deterministic in-memory demo repository otherwise.
- `backend/schema.sql`: PostgreSQL schema for users, devices, components, repair outcomes, and audit events.
- Compatibility decisions are made by explicit RAM/SSD rules in `backend/app.py`; unknown specifications are reported as unknown rather than guessed.

## Run locally

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:FLASK_DEBUG="1"
python app.py
```

The API runs at `http://localhost:5000`. Add `DATABASE_URL` to use PostgreSQL; otherwise demo data is loaded in memory.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal. The frontend defaults to `http://localhost:5000/api` and can be changed with `VITE_API_URL`.

Demo sign-in accepts any email and password, then assigns the `technician` role unless a different role is selected in the sign-in form.

## Key API routes

`GET /api/summary`, `GET/POST /api/components`, `GET /api/components/:id`, `POST /api/components/:id/passport`, `GET /api/devices`, `POST /api/compatibility/check`, `POST /api/repairs`, and `GET /api/graph`.

## Production hardening checklist

- Replace demo authentication with OIDC/JWT and password hashing.
- Run migrations from `schema.sql` through Alembic.
- Add object storage for passport photos and a managed PostgreSQL instance.
- Add rate limiting, structured logging, CSRF protection, and background QR/passport jobs.
