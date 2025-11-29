# IdleDuelist Deployment Guide

## Overview
Deploy IdleDuelist to Fly.io using the included `Dockerfile`, `fly.toml`, and GitHub Actions workflow. Fly builds the container image, provisions machines close to your players, and keeps HTTPS certificates up to date automatically.

## Prerequisites
- Fly.io account: https://fly.io
- Fly CLI (`flyctl`): https://fly.io/docs/hands-on/install-flyctl/
- GitHub repository linked to this project
- `FLY_API_TOKEN` GitHub secret (create via `fly auth token`)
- Optional: Custom domain you control

## 1. Configure the Fly app
1. Install `flyctl` and authenticate: `fly auth login`
2. Update `fly.toml`:
   - Set `app = "<your-app-name>"` to the Fly app you created (e.g., `idleduelist`).
   - Adjust `primary_region` if you need a different data center.
3. If you have not created the app yet, run `fly apps create <your-app-name>` or `fly launch --no-deploy` (this repo already contains the Dockerfile/fly.toml, so no files will be generated).
4. Commit the updated `fly.toml` (or keep `FLY_APP_NAME` as a GitHub Secret to override the name at deploy time).

## 2. Provision PostgreSQL (required)
1. Create a Fly Postgres cluster (shared CPU is fine to start):
   ```bash
   fly postgres create --name idleduelist-db --organization personal --region iad
   ```
2. Attach it to the app (this sets `DATABASE_URL` for you):
   ```bash
   fly postgres attach --postgres-app idleduelist-db --app <your-app-name>
   ```
3. Confirm the secret exists: `fly secrets list | grep DATABASE_URL`

## 3. Provision Redis (optional but recommended)
Fly offers a managed Redis service in private beta via `fly redis create`. You can also point to Upstash, Redis Cloud, or any external provider:
```bash
fly secrets set REDIS_URL=redis://:<password>@<host>:<port>/0
```
If `REDIS_URL` is not provided the app falls back to in-memory storage, which limits horizontal scaling.

## 4. Configure application secrets
Run the following once per environment:
```bash
fly secrets set \
  ENVIRONMENT=production \
  JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))") \
  CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```
Optional secrets:
- `REDIS_URL` – if using an external Redis instance
- `TELEMETRY_SAMPLE_RATE`, `LOG_FILE`, etc. (see `app/core/config.py`)

## 5. GitHub Actions deployment
This repository includes `.github/workflows/deploy.yml`, which:
1. Installs dependencies and runs `pytest`
2. Installs `flyctl`
3. Deploys with `flyctl deploy --remote-only --detach`

To enable it:
1. In your GitHub repo go to **Settings → Secrets and variables → Actions**
2. Add `FLY_API_TOKEN` (from `fly auth token`)
3. (Optional) Add `FLY_APP_NAME` if you want to override the name stored in `fly.toml`
4. Push to `main` (or `master`). The workflow deploys automatically when the tests pass.

Manual deploys:
```bash
flyctl deploy --remote-only
```
(Requires running `fly auth login` locally.)

## 6. Domains & HTTPS
- Every Fly app receives a `https://<app>.fly.dev` domain automatically with TLS.
- To add your own domain:
  ```bash
  flyctl certificates add yourdomain.com
  # Follow the DNS instructions shown (CNAME/AAAA records)
  ```
- Update `CORS_ORIGINS` to include each domain you serve.

## Local development
- Uses SQLite (`idleduelist.db`) by default
- Redis is optional. Without `REDIS_URL` the game uses an in-memory queue.
- To test with PostgreSQL/Redis locally, use Docker:
  ```bash
  docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=devpass postgres
  docker run -d -p 6379:6379 redis
  export DATABASE_URL=postgresql://postgres:devpass@localhost:5432/postgres
  export REDIS_URL=redis://localhost:6379/0
  python start_server.py
  ```

## Verification checklist
1. `fly status` shows at least one `app` machine running
2. `fly logs` has "✓ PostgreSQL connection successful"
3. `https://<app>.fly.dev/health` returns `{"status": "healthy", ...}`
4. `/metrics` exposes request counters and timing stats
5. `/api/register` and `/api/login` behave correctly in production

## Troubleshooting on Fly
- **Database errors**: `fly postgres connect -a idleduelist-db` to inspect, or check `DATABASE_URL` via `fly secrets list`
- **Redis unavailable**: verify `REDIS_URL` secret and external provider status; the app logs when it falls back to in-memory mode
- **Build failures**: inspect the GitHub Actions log (Docker build) or run `flyctl deploy --local-only` to reproduce
- **Port issues**: Fly injects `PORT`; make sure your config/listener uses `${PORT:-8080}` (handled in the Dockerfile)
- **Rolling back**: `flyctl releases list` and `flyctl releases info <version>`; deploy an older image with `flyctl deploy --image <registry-image>` if needed

## Scaling tips
- Increase machine size: `fly scale vm shared-cpu-2x` (or another plan)
- Add more instances: `fly scale count 2`
- Autoscaling: `fly autoscale set min=1 max=3` (machines platform)
- Database: upgrade the Fly Postgres plan or connect to an external managed Postgres if you outgrow shared CPU

## Security notes
- Store secrets only via `fly secrets set` (never commit `.env` with production values)
- Enforce strong `JWT_SECRET_KEY` values and rotate regularly
- Limit `CORS_ORIGINS` to trusted domains
- Fly terminates TLS and forwards requests over WireGuard-encrypted private networking to your machines

## Support & references
- Fly documentation: https://fly.io/docs/
- Fly community forum: https://community.fly.io
- Fly status page: https://status.flyio.net/

Once configured, every push to `main` runs tests and deploys the latest build to Fly.io automatically.
