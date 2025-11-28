# IdleDuelist API Documentation

## Base URL
- Development: `http://localhost:8000`
- Production: `https://yourdomain.com`

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Endpoints

### Health & Monitoring

#### GET /health
Returns detailed health status of all dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "version": "2.0.0",
  "environment": "production",
  "checks": {
    "database": {
      "status": "healthy",
      "type": "PostgreSQL",
      "configured": "yes",
      "response_time_ms": 5.23
    },
    "redis": {
      "status": "healthy",
      "configured": "yes",
      "response_time_ms": 1.45
    }
  }
}
```

#### GET /health/live
Simple liveness probe. Returns `{"status": "alive"}` if server is running.

#### GET /health/ready
Readiness probe. Returns `{"status": "ready"}` if server can accept requests.

#### GET /metrics
Returns server metrics for monitoring.

**Response:**
```json
{
  "requests": {
    "total": 1000,
    "errors": 5,
    "success_rate": 99.5
  },
  "response_times": {
    "average_ms": 45.2,
    "p95_ms": 120.5
  },
  "database": {
    "active_connections": 5
  },
  "redis": {
    "connected": true,
    "used_memory_mb": 12.5
  },
  "uptime_seconds": 3600
}
```

### Authentication

#### POST /api/register
Register a new user account.

**Request:**
```json
{
  "username": "player123",
  "password": "securepassword",
  "email": "player@example.com"
}
```

**Validation:**
- Username: 3-50 characters, alphanumeric and underscores only
- Password: Minimum 6 characters
- Email: Optional, must be valid email format

**Rate Limit:** 5 requests per minute per IP

#### POST /api/login
Login and receive JWT tokens.

**Request:**
```json
{
  "username": "player123",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "success": true,
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user_id": "...",
  "username": "player123",
  "has_character": true,
  "character_id": "...",
  "character_name": "MyCharacter"
}
```

**Rate Limit:** 10 requests per minute per IP

#### POST /api/auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "..."
}
```

### Characters

#### GET /api/character/list
Get list of characters for the authenticated user.

**Response:**
```json
{
  "success": true,
  "characters": [
    {
      "id": "...",
      "name": "MyCharacter",
      "level": 10,
      "exp": 5000
    }
  ]
}
```

#### GET /api/character/{character_id}
Get detailed character information.

**Response:**
```json
{
  "success": true,
  "character": {
    "id": "...",
    "name": "MyCharacter",
    "level": 10,
    "exp": 5000,
    "stats": {...},
    "equipment": {...},
    "inventory": [...],
    "combat_stats": {...},
    "gold": 1000
  }
}
```

#### POST /api/character/create
Create a new character.

**Request:**
```json
{
  "name": "NewCharacter"
}
```

**Validation:**
- Name: 1-50 characters, alphanumeric, underscores, and spaces only

### Combat

#### POST /api/combat/start
Start a combat encounter.

**Request:**
```json
{
  "character_id": "...",
  "enemy_id": "...",  // For PvE
  "opponent_id": "..."  // For PvP
}
```

**Response:**
```json
{
  "success": true,
  "combat_id": "...",
  "combat_state": {...}
}
```

**Rate Limit:** 30 requests per minute per user

#### GET /api/combat/{combat_id}
Get current combat state.

#### POST /api/combat/{combat_id}/action
Perform an action in combat.

**Request:**
```json
{
  "action_type": "attack",  // "attack", "ability", or "defend"
  "ability_id": "...",  // Required for ability actions
  "target": "player1"  // Optional
}
```

## Error Responses

All errors follow a standardized format:

```json
{
  "success": false,
  "error": {
    "type": "validation_error",
    "message": "Invalid request data",
    "details": {
      "errors": [
        {
          "field": "username",
          "message": "Username is required",
          "type": "value_error.missing"
        }
      ]
    }
  }
}
```

## Rate Limiting

- Default: 1000 requests per hour per IP
- Registration: 5 requests per minute
- Login: 10 requests per minute
- Combat start: 30 requests per minute

Rate limit exceeded responses include a `Retry-After` header indicating when to retry.

## Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required or invalid token
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

