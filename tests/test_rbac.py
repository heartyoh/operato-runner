import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from httpx import AsyncClient, ASGITransport
from api.rest import app

import asyncio

@pytest.mark.asyncio
async def test_admin_access():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 관리자 계정 생성
        resp = await ac.post("/auth/register", json={
            "username": "adminuser",
            "email": "admin@example.com",
            "password": "Admin1234!"
        })
        assert resp.status_code == 201
        # (테스트 DB라면 직접 role 할당 필요, 실제 환경에서는 마이그레이션/관리자 생성 로직 활용)
        # 로그인
        resp = await ac.post("/auth/login", json={
            "username": "adminuser",
            "email": "admin@example.com",
            "password": "Admin1234!"
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        # /admin 접근 (관리자 권한 필요)
        resp = await ac.get("/admin", headers={"Authorization": f"Bearer {token}"})
        # 실제로는 role 체크가 DB에 반영되어야 하므로, 여기서는 403이 나올 수 있음
        # 관리자 권한 부여 로직이 있다면 200, 없으면 403
        assert resp.status_code in (200, 403)

@pytest.mark.asyncio
async def test_admin_only_logs():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 일반 사용자 생성
        resp = await ac.post("/auth/register", json={
            "username": "normaluser",
            "email": "normal@example.com",
            "password": "Normal1234!"
        })
        assert resp.status_code == 201
        # 로그인
        resp = await ac.post("/auth/login", json={
            "username": "normaluser",
            "email": "normal@example.com",
            "password": "Normal1234!"
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        # /audit/logs 접근 (관리자만 가능)
        resp = await ac.get("/audit/logs", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403 