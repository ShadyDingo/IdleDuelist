# Production Deployment Checklist

## Pre-Deployment

### Environment Variables
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `JWT_SECRET_KEY` (minimum 32 characters, use strong random value)
- [ ] Set `CORS_ORIGINS` to your actual domain(s) (comma-separated)
- [ ] Set `DATABASE_URL` for PostgreSQL connection
- [ ] Set `REDIS_URL` for Redis connection (optional but recommended)

### Security
- [ ] Verify CORS_ORIGINS is set and does not include "*"
- [ ] Verify JWT_SECRET_KEY is strong (use: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] Review rate limiting configuration
- [ ] Ensure HTTPS is enabled (Railway handles this automatically)

### Database
- [ ] PostgreSQL service is running in Railway
- [ ] DATABASE_URL is correctly configured
- [ ] Database migrations have run successfully
- [ ] Create initial database backup

### Monitoring
- [ ] Set up monitoring/alerts for `/health` endpoint
- [ ] Configure log aggregation (if needed)
- [ ] Set up error tracking (Sentry, etc.)

## Post-Deployment Verification

### Health Checks
- [ ] Verify `/health` endpoint returns `"status": "healthy"`
- [ ] Verify `/health/live` endpoint responds
- [ ] Verify `/health/ready` endpoint responds
- [ ] Check `/metrics` endpoint for baseline metrics

### Functionality Tests
- [ ] Test user registration
- [ ] Test user login
- [ ] Test character creation
- [ ] Test PvE combat
- [ ] Test PvP combat
- [ ] Test equipment management
- [ ] Test store functionality

### Performance
- [ ] Check response times on `/metrics`
- [ ] Verify database connection pooling is working
- [ ] Check Redis connection (if configured)
- [ ] Monitor error rates

## Ongoing Maintenance

### Daily
- [ ] Review error logs
- [ ] Check `/metrics` for anomalies
- [ ] Monitor database connection count

### Weekly
- [ ] Review and rotate logs if needed
- [ ] Check database backup integrity
- [ ] Review performance metrics

### Monthly
- [ ] Run database backup
- [ ] Review and update dependencies
- [ ] Review security logs
- [ ] Test disaster recovery procedures

## Backup & Recovery

### Database Backups
Backups can be created using:
```bash
python backup_database.py
```

Backups are stored in the `backups/` directory and automatically cleaned up after 7 days.

### Restore Procedure
1. Stop the application
2. Restore database from backup
3. Verify database integrity
4. Restart application
5. Verify health endpoints

## Troubleshooting

See `TROUBLESHOOTING.md` for common issues and solutions.

