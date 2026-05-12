# Advanced Financial Advisor UI

A modern, production-ready web interface for the Financial Advisor backend with real-time streaming chat.

## Features

✨ **Modern Design** — ChatGPT-inspired dark theme with smooth animations
🔄 **Real-time Streaming** — Live chat responses with token-by-token updates  
💬 **Session Management** — Multiple independent chat conversations
📊 **Portfolio Integration** — Select portfolios and view live metrics
📱 **Fully Responsive** — Works perfectly on desktop and mobile
⚡ **Vanilla JavaScript** — No frameworks, fast and lightweight

## Quick Start

### 1. Backend Running
```bash
cd /home/sandeshpatil/Downloads/Financial-Advisor/Financial-Advisor
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8050
```

### 2. Start Web UI
```bash
cd /home/sandeshpatil/Downloads/Financial-Advisor/Financial-Advisor/UI
python3 -m http.server 8080
```

### 3. Open Browser
```
http://localhost:8080
```

## File Structure

```
UI/
├── index.html          # Main HTML entry point
├── css/
│   └── styles.css      # All styles (dark theme, animations, responsive)
├── js/
│   ├── config.js       # Configuration (API URL)
│   ├── api.js          # API client with streaming support
│   ├── ui.js           # UI state and rendering logic
│   └── app.js          # Main app initialization and events
└── README.md           # This file
```

## Run the UI

1. Start the backend API normally.

2. Run the UI from the UI folder:

```bash
cd UI
python3 -m http.server 8080
```

3. Open browser at:

```bash
http://localhost:8080
```

## Backend endpoints used

- `GET /api/v1/health`
- `GET /api/v1/portfolios`
- `GET /api/v1/portfolios/{portfolio_id}`
- `POST /api/v1/chat`
- `POST /api/v1/chat/title`

## Configuration

The UI uses `UI_API_BASE_URL` if set, otherwise it defaults to:

```bash
http://localhost:8000/api/v1
```

## Configuration

Edit `js/config.js` to change the backend URL:

```js
const CONFIG = {
    API_BASE_URL: "http://localhost:8050/api/v1",
};
```

## Deploy on Render

This repo uses two Docker services on Render:

- `financial-advisor-backend` — serves the FastAPI API
- `financial-advisor-ui` — serves the static HTML/CSS/JS UI

It also uses Render-managed databases for production:

- `financial-advisor-db` — PostgreSQL for app data
- `financial-advisor-redis` — Redis for session storage

### Back-end service

1. Create a new web service using `Dockerfile` at the repo root.
2. Set `Start Command` to the default container command, or leave it empty.
3. Configure environment variables:
   - `DATABASE_URL` from the `financial-advisor-db` connection string
   - `REDIS_URL` from the `financial-advisor-redis` connection string
   - `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`

### UI service

1. Create a second web service using `UI/web/Dockerfile`.
2. Set `Start Command` to the default container command, or leave it empty.
3. Set `UI_API_BASE_URL` to your backend URL, for example:
   - `https://financial-advisor-backend.onrender.com/api/v1`

### Database services

Use Render's dashboard or `render.yaml` to create:

- PostgreSQL service named `financial-advisor-db`
- Redis service named `financial-advisor-redis`

Render can inject the connection strings into your backend service environment.

### Notes

- Do not use SQLite on Render; the backend must use PostgreSQL.
- The UI is static and only needs `UI_API_BASE_URL`.
- Langfuse is external, so you only need to provide its API keys and endpoint.

Then access the UI at the Render URL for `financial-advisor-ui`.

## API Endpoints Used

- `GET /api/v1/health` — Backend health check
- `GET /api/v1/portfolios` — List all portfolios
- `GET /api/v1/portfolios/{id}` — Get portfolio details
- `POST /api/v1/chat` — Stream chat response (SSE)
- `POST /api/v1/chat/complete` — Non-streaming response
- `POST /api/v1/chat/title` — Generate chat session title

## Streaming Chat

The UI uses **Server-Sent Events (SSE)** for real-time streaming. The backend sends tokens as they're generated, and the UI displays them incrementally for a smooth, responsive experience.

## Design Inspiration

The UI is inspired by the existing chat frontend architecture with:
- Dark theme (#202123, #1a1a1a backgrounds)
- Green accent color (#19c37d)
- Clean chat bubbles and session history
- Professional typography and spacing

But built as a pure HTML/CSS/JS application for better performance and customization.
