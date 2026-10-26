# Employee Assistant Server

FastAPI and PostgreSQL server with a React/Vite administration UI. PostgreSQL is the only data store; Android and the UI use the REST API only.

## Setup and run

1. Install PostgreSQL, Python 3.11+, Git, and Node.js on the server, then clone this repository.
2. Create the environment and install the backend:
   ```bash
   python3 -m venv .venv
   . .venv/bin/activate
   pip install -r api/requirements.txt
   cp .env.example .env
   ```
3. Edit `.env` with the PostgreSQL connection settings and set a strong `ADMIN_INITIAL_PASSWORD`. Run `chmod +x scripts/*.sh`, then create tables with `./scripts/setup_database.sh`. The password is used only once to create the `admin` account; it is stored as a hash, not in plaintext.
4. Build the UI (Node is needed only here):
   ```bash
   cd admin-ui && npm install && npm run build && cd ..
   ```
5. Start locally with `cd api && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`. Open `/` for the UI, `/docs` for API documentation, and `/health` for service health.
6. For systemd, edit the paths and `User` in `deployment/employee-assistant-api.service`, copy it to `/etc/systemd/system/`, then run:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now employee-assistant-api
   ```
7. To update: `git pull`, activate the virtual environment and run `pip install -r api/requirements.txt`, rebuild `admin-ui`, then `sudo systemctl restart employee-assistant-api`.
8. Back up with `./scripts/backup.sh`. Restore a dump using `./scripts/restore.sh backups/<file>.dump`.

For an existing deployment, apply `database/migrations/20260909_master_admin_auth.sql` once before restarting the API, then set `ADMIN_INITIAL_PASSWORD` in `.env` for the first restart. After logging in, remove that variable if desired; it never replaces an existing password. Set `AUTH_COOKIE_SECURE=true` when serving the application over HTTPS.

## Admin UI API routing

The production UI is built into `api/static` and served by FastAPI, so browser
requests use the same-origin `/api/rest` path. When running the Vite UI with
`npm run dev`, Vite proxies `/api/*` to `http://127.0.0.1:8000` by default.
Set `VITE_API_PROXY_TARGET` to change that development target. If the UI is
hosted separately in production, configure its reverse proxy to forward
`/api/` to FastAPI, or set the build-time `VITE_API_BASE_URL` to the FastAPI
origin (with matching CORS configuration).

No records are inserted by setup. Deactivation is a soft delete; restoring is always explicit.
