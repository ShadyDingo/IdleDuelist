# IdleDuelist Deployment Guide

## Overview
This guide covers deploying IdleDuelist to Railway with PostgreSQL, Redis, and custom domain setup.

## Prerequisites
- Railway account (https://railway.app)
- Domain name (optional, for custom domain)
- Git repository (optional, for automatic deployments)

## Railway Setup

### 1. Create New Project
1. Log into Railway dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo" or "Empty Project"

### 2. Add Services

#### PostgreSQL Database
1. In your Railway project, click "New"
2. Select "Database" → "Add PostgreSQL"
3. Railway will automatically create a PostgreSQL instance
4. Note the `DATABASE_URL` connection string (automatically set as environment variable)

#### Redis Cache
1. In your Railway project, click "New"
2. Select "Database" → "Add Redis"
3. Railway will automatically create a Redis instance
4. Note the `REDIS_URL` connection string (automatically set as environment variable)

#### Web Service
1. In your Railway project, click "New"
2. Select "GitHub Repo" or "Empty Service"
3. If using GitHub, connect your repository
4. Railway will auto-detect Python and use the `railway.json` configuration

### 3. Environment Variables

Set these in Railway dashboard under your web service → Variables:

**Required:**
- `JWT_SECRET_KEY` - A secure random string (minimum 32 characters). Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `ENVIRONMENT` - Set to `production`

**Optional (for custom domain):**
- `CORS_ORIGINS` - Comma-separated list of allowed origins (e.g., `https://yourdomain.com,https://www.yourdomain.com`)
- `JWT_ALGORITHM` - Defaults to `HS256` (usually fine)

**Auto-configured by Railway:**
- `DATABASE_URL` - Automatically set when PostgreSQL service is added
- `REDIS_URL` - Automatically set when Redis service is added
- `PORT` - Automatically set by Railway

### 4. Domain Setup

#### Using Railway Subdomain
Railway automatically provides a subdomain like `yourproject.up.railway.app`. This works immediately with HTTPS.

#### Using Custom Domain
1. In Railway dashboard, go to your web service → Settings → Domains
2. Click "Add Domain"
3. Enter your domain (e.g., `yourdomain.com`)
4. Railway will provide DNS records to configure:
   - **CNAME record**: Point your domain to Railway's provided domain
   - Or **A record**: Use Railway's IP address (if provided)
5. Configure DNS at your domain registrar:
   - Add CNAME: `yourdomain.com` → `yourproject.up.railway.app`
   - Or add A record: `yourdomain.com` → Railway's IP
6. Railway automatically provisions SSL certificate (may take a few minutes)
7. Update `CORS_ORIGINS` environment variable to include your domain

### 5. Deployment

Railway will automatically:
- Install dependencies from `requirements.txt`
- Run database migrations on startup
- Start the server using the command in `railway.json`

Monitor deployment in Railway dashboard → Deployments tab.

## Local Development

For local development, the app uses:
- SQLite database (`idleduelist.db`)
- In-memory state (no Redis required)

To test with PostgreSQL/Redis locally:
1. Install Docker
2. Run PostgreSQL: `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=test postgres`
3. Run Redis: `docker run -d -p 6379:6379 redis`
4. Set environment variables:
   - `DATABASE_URL=postgresql://postgres:test@localhost:5432/idleduelist`
   - `REDIS_URL=redis://localhost:6379`
   - `JWT_SECRET_KEY=your-local-secret-key`

## Verification

After deployment:
1. Check health endpoint: `https://yourdomain.com/health`
2. Should return: `{"status": "healthy", "database": "connected", "redis": "connected", ...}`
3. Test login/registration at: `https://yourdomain.com/`
4. Verify JWT tokens are being generated and stored

## Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL service is running in Railway
- Ensure database migrations ran successfully (check logs)

### Redis Connection Issues
- Verify `REDIS_URL` is set correctly
- Check Redis service is running in Railway
- App will fall back to in-memory storage if Redis unavailable

### Authentication Issues
- Verify `JWT_SECRET_KEY` is set (must be at least 32 characters)
- Check browser console for token errors
- Verify CORS settings allow your domain

### Static Files Not Loading
- Ensure `assets/` directory is included in deployment
- Check Railway build logs for file copy issues

## Scaling

For higher traffic:
1. Railway automatically scales based on usage
2. Consider upgrading PostgreSQL plan for more connections
3. Redis plan can be upgraded for more memory
4. Monitor Railway dashboard for resource usage

## Security Notes

- Never commit `JWT_SECRET_KEY` to git
- Use strong, unique `JWT_SECRET_KEY` in production
- Restrict `CORS_ORIGINS` to your actual domain(s)
- Railway handles SSL/HTTPS automatically
- Database and Redis connections are encrypted in transit

## Support

For Railway-specific issues, check:
- Railway documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

