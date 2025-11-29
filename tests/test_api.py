#!/usr/bin/env python3
"""
API endpoint tests
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

class TestHealthEndpoints:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
    
    def test_liveness_endpoint(self):
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"
    
    def test_metrics_endpoint(self):
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "requests" in data
        assert "response_times" in data

class TestAuthEndpoints:
    def test_register_missing_fields(self):
        response = client.post("/api/register", json={})
        assert response.status_code in [422, 400]  # Validation error
    
    def test_login_missing_fields(self):
        response = client.post("/api/login", json={})
        assert response.status_code in [422, 400]  # Validation error
    
    def test_register_invalid_username(self):
        response = client.post("/api/register", json={
            "username": "ab",  # Too short
            "password": "password123"
        })
        assert response.status_code == 422  # Validation error
    
    def test_register_invalid_password(self):
        response = client.post("/api/register", json={
            "username": "testuser",
            "password": "123"  # Too short
        })
        assert response.status_code == 422  # Validation error


class TestPlayerEndpoints:
    def test_profile_requires_auth(self):
        response = client.get("/api/player/profile")
        assert response.status_code == 401

    def test_progress_requires_auth(self):
        response = client.get("/api/player/progress/test-character")
        assert response.status_code == 401

    def test_matches_requires_auth(self):
        response = client.get("/api/player/matches")
        assert response.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

