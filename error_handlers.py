#!/usr/bin/env python3
"""
Error handlers and standardized error responses
"""
import os
import uuid
import logging
import traceback
from typing import Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

def create_error_response(
    message: str,
    status_code: int = 500,
    error_type: str = "internal_error",
    details: Optional[dict] = None
) -> JSONResponse:
    """Create a standardized error response"""
    response = {
        "success": False,
        "error": {
            "type": error_type,
            "message": message,
        }
    }
    if details:
        response["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=response)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error on {request.url.path}: {errors}")
    return create_error_response(
        message="Invalid request data",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type="validation_error",
        details={"errors": errors}
    )

async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    logger.warning(f"Rate limit exceeded for {request.client.host} on {request.url.path}")
    return create_error_response(
        message="Rate limit exceeded. Please try again later.",
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        error_type="rate_limit_exceeded",
        details={"retry_after": exc.retry_after}
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    error_id = str(uuid.uuid4())
    logger.error(
        f"Unhandled exception {error_id} on {request.url.path}: {str(exc)}\n"
        f"Traceback: {traceback.format_exc()}"
    )
    
    # In production, don't expose internal error details
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
    message = "An internal server error occurred"
    details = {"error_id": error_id} if is_production else {
        "error_id": error_id,
        "error": str(exc),
        "traceback": traceback.format_exc()
    }
    
    return create_error_response(
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="internal_error",
        details=details
    )

