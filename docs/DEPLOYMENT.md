# Sentinel AI v1.0.0 — Production Deployment Guide

This guide covers production deployment of Sentinel AI on free/tier cloud services: **Vercel** (Frontend), **Render** (Backend), **Neon** (PostgreSQL), and **Upstash** (Redis).

---

## 1. Neon PostgreSQL Database
1. Create a project at [Neon.tech](https://neon.tech).
2. Copy your Connection String (`postgres://user:pass@ep-xyz.neon.tech/neondb?sslmode=require`).
3. Set `DATABASE_URL` in your backend environment configuration.

---

## 2. Upstash Redis Caching
1. Create a database at [Upstash.com](https://upstash.com).
2. Copy your `REDIS_URL` (`rediss://default:pass@region.upstash.io:6379`).
3. Set `REDIS_URL` in your backend environment configuration.

---

## 3. Render Web Service (Backend API)
1. Connect your repository to [Render.com](https://render.com).
2. Select **Web Service**, environment **Python 3.10**.
3. Set Build Command: `pip install -r backend/requirements.txt`.
4. Set Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 10000`.
5. Add Environment Variables:
   - `DATABASE_URL`
   - `REDIS_URL`
   - `JWT_SECRET_KEY`
   - `CORS_ORIGINS`

---

## 4. Vercel Project (Frontend UI)
1. Import your project repository into [Vercel.com](https://vercel.com).
2. Set Root Directory to `frontend`.
3. Set Framework Preset to **Next.js**.
4. Set Environment Variable:
   - `NEXT_PUBLIC_API_URL` -> Your Render backend URL (`https://sentinel-backend.onrender.com/api/v1`).
5. Deploy.
