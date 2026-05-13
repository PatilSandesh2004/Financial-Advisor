# Render Deployment Guide

This document explains how to deploy the Financial Advisor app to Render using Redis and PostgreSQL.

## Overview

The app is split into two web services:

1. `financial-advisor-backend` — FastAPI backend service
2. `financial-advisor-ui` — Static HTML/CSS/JS frontend service

And two managed data services:

- `financial-advisor-db` — PostgreSQL database
- `financial-advisor-redis` — Redis cache/session store

> Important: Render cannot use your laptop `localhost` services. If you deploy to Render, Redis and Postgres must be reachable from Render.

---

## 1. Connect your GitHub repo

1. Sign in to Render: `https://render.com`
2. Create a new service
3. Connect your GitHub repository containing this project
4. Choose the branch you want to deploy (for example `deployment`)

---

## 2. Create managed databases

### PostgreSQL

1. Create a new Render service
2. Choose `Postgres`
3. Name it `financial-advisor-db`
4. Select the `Starter` plan or the plan you need
5. Create the database

Render will provide a connection string like:

```text
postgres://user:password@host:5432/dbname
```

### Redis

1. Create a new Render service
2. Choose `Redis`
3. Name it `financial-advisor-redis`
4. Select the `Starter` plan or the plan you need
5. Create Redis

Render will provide a connection URL like:

```text
redis://:password@host:6379/0
```

---

## 3. Create the backend service

### Service settings

- Type: `Web Service`
- Name: `financial-advisor-backend`
- Environment: `Docker`
- Dockerfile Path: `Dockerfile`
- Branch: your repo branch

### Environment variables for backend

Add these environment variables to the backend service:

- `DATABASE_URL`
  - Use the Postgres connection string from `financial-advisor-db`
- `REDIS_URL`
  - Use the Redis connection string from `financial-advisor-redis`
- `LANGFUSE_PUBLIC_KEY`
  - Your Langfuse public key
- `LANGFUSE_SECRET_KEY`
  - Your Langfuse secret key
- `LANGFUSE_BASE_URL`
  - Usually `https://cloud.langfuse.com`

Optional but recommended if the app requires it:

- `API_BASE_URL`
  - `https://financial-advisor-backend.onrender.com/api/v1`

### Notes

- The backend service uses `DATABASE_URL` for PostgreSQL.
- The backend service uses `REDIS_URL` for Redis.
- If `DATABASE_URL` or `REDIS_URL` is missing, the app may fail at runtime.

---

## 4. Create the UI service

### Service settings

- Type: `Web Service`
- Name: `financial-advisor-ui`
- Environment: `Docker`
- Dockerfile Path: `UI/Dockerfile`
- Branch: same repo branch

### Environment variables for UI

- `UI_API_BASE_URL`
  - Set this to the backend API URL:
    - `https://financial-advisor-backend.onrender.com/api/v1`

### Notes

- The UI is static and only needs the backend URL.
- The UI must call the backend through the public Render address, not `localhost`.

---

## 5. Deploy order

1. Deploy `financial-advisor-db`
2. Deploy `financial-advisor-redis`
3. Deploy `financial-advisor-backend`
4. Deploy `financial-advisor-ui`

If Render builds the backend before the databases are ready, restart the backend after databases are available.

---

## 6. Confirm your URLs

After deployment, the service URLs will be:

- Backend: `https://financial-advisor-backend.onrender.com/api/v1`
- UI: `https://financial-advisor-ui.onrender.com`

If the service names are different, replace the subdomain accordingly.

---

## 7. Verification

1. Open the backend health endpoint in the browser or via curl:

```bash
curl https://financial-advisor-backend.onrender.com/api/v1/health
```

2. Open the UI URL in the browser:

```text
https://financial-advisor-ui.onrender.com
```

3. Type a chat message and verify the app responds.

---

## 8. Local development vs Render

- `docker compose` on your laptop is for local development only.
- Render is separate cloud hosting.
- Local PostgreSQL/Redis or local Docker cannot be used by Render unless the services are public and accessible.

Use Render-managed Postgres and Redis for a clean deployment.
