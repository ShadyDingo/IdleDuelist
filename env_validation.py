#!/usr/bin/env python3
"""
Environment variable validation on startup
"""
import os
import sys
import logging

logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables"""
    errors = []
    warnings = []
    
    environment = os.getenv("ENVIRONMENT", "development").lower()
    is_production = environment == "production"
    
    # Required in production
    if is_production:
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret:
            errors.append("JWT_SECRET_KEY is required in production")
        elif len(jwt_secret) < 32:
            errors.append("JWT_SECRET_KEY must be at least 32 characters in production")
        
        cors_origins = os.getenv("CORS_ORIGINS", "")
        if not cors_origins or cors_origins == "*":
            errors.append("CORS_ORIGINS must be explicitly set in production (cannot be * or empty)")
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            warnings.append("DATABASE_URL not set - will use SQLite (data will NOT persist)")
    
    # Validate JWT secret in development (warn if weak)
    if not is_production:
        jwt_secret = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-min-32-chars")
        if jwt_secret == "your-secret-key-change-in-production-min-32-chars" or len(jwt_secret) < 32:
            warnings.append("JWT_SECRET_KEY is weak - this is OK for development but must be >= 32 chars in production")
    
    # Log warnings
    for warning in warnings:
        logger.warning(f"⚠ {warning}")
    
    # Log errors and exit if in production
    if errors:
        for error in errors:
            logger.error(f"❌ {error}")
        if is_production:
            logger.error("Environment validation failed - cannot start in production mode")
            sys.exit(1)
        else:
            logger.warning("Environment validation failed - continuing in development mode")
    
    return len(errors) == 0

