# Troubleshooting Guide

## Common Issues

### Database Connection Errors

**Error:** `Failed to connect to PostgreSQL`

**Solutions:**
1. Verify DATABASE_URL is set correctly in Railway
2. Check PostgreSQL service is running in Railway dashboard
3. Verify connection string format: `postgresql://user:password@host:port/database`
4. Check firewall/network settings

**Error:** `Using SQLite (data will NOT persist on Railway!)`

**Solutions:**
1. Add PostgreSQL service in Railway
2. Set DATABASE_URL environment variable
3. Restart the application

### Redis Connection Issues

**Error:** `Redis connection failed (using in-memory storage)`

**Impact:** Combat states and caching will use in-memory storage, which means:
- Data is lost on server restart
- Multiple server instances won't share state
- Not suitable for production scaling

**Solutions:**
1. Add Redis service in Railway
2. Set REDIS_URL environment variable
3. Restart the application

### Authentication Errors

**Error:** `JWT_SECRET_KEY is required in production`

**Solution:**
Set JWT_SECRET_KEY environment variable:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Error:** `Invalid or expired token`

**Solutions:**
1. Check token hasn't expired (default: 24 hours for access token)
2. Verify JWT_SECRET_KEY matches between server instances
3. Check token format in Authorization header: `Bearer <token>`
4. Try refreshing token using `/api/auth/refresh`

### CORS Errors

**Error:** CORS policy blocking requests

**Solutions:**
1. Verify CORS_ORIGINS is set to your domain
2. Check it doesn't include trailing slashes
3. Format: `https://yourdomain.com,https://www.yourdomain.com`
4. In development, can use `*` but NOT in production

### Rate Limiting

**Error:** `429 Too Many Requests`

**Solutions:**
1. Wait for the rate limit window to reset
2. Check Retry-After header for wait time
3. Review rate limits:
   - Default: 1000/hour
   - Registration: 5/minute
   - Login: 10/minute
   - Combat: 30/minute

### Combat Issues

**Error:** Combat state not found

**Solutions:**
1. Check Redis is configured (combat states stored in Redis)
2. Combat states expire after 1 hour
3. Verify combat_id is correct
4. Check logs for combat state creation errors

**Error:** EXP not being awarded

**Solutions:**
1. Check database logs for errors
2. Verify combat completed successfully
3. Check character EXP value after combat
4. Review end_combat function logs

### Equipment Issues

**Error:** Weapon icons not showing

**Solutions:**
1. Verify weapon_type field exists on equipment items
2. Check assets/weapons directory has all icon files
3. Verify browser console for 404 errors
4. Check icon paths in network tab

### Performance Issues

**Symptom:** Slow response times

**Solutions:**
1. Check `/metrics` endpoint for bottlenecks
2. Review database query performance
3. Verify connection pooling is working
4. Check Redis is caching properly
5. Review server resource usage in Railway

**Symptom:** High error rates

**Solutions:**
1. Check error logs for patterns
2. Review `/metrics` for error counts
3. Check database connection limits
4. Verify all services are healthy via `/health`

## Log Locations

### Application Logs
- Production: `idleduelist.log` (rotating, max 10MB, 5 backups)
- Development: Console output

### Railway Logs
- Available in Railway dashboard under "Deployments" → "View Logs"

### Database Logs
- PostgreSQL: Check Railway PostgreSQL service logs
- SQLite: No separate logs (errors appear in application logs)

## Health Check Endpoints

Use these to diagnose issues:

1. **`/health`** - Detailed status of all dependencies
2. **`/health/live`** - Simple liveness check
3. **`/health/ready`** - Readiness check (verifies database)
4. **`/metrics`** - Performance metrics

## Getting Help

1. Check application logs for detailed error messages
2. Review Railway deployment logs
3. Check `/health` endpoint for service status
4. Review this troubleshooting guide
5. Check GitHub issues (if applicable)

## Debug Mode

In development, set `ENVIRONMENT=development` to:
- Enable detailed error messages
- Include stack traces in error responses
- Use console logging instead of file logging
- Allow CORS from any origin

**Never use development mode in production!**
