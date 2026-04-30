# Autonomous Financial Advisor

A  financial advisor that explains Indian portfolio movements through a causal chain:
**Macro News → Sector Trend → Stock Impact → Portfolio Impact**

Built with FastAPI (backend) + Streamlit (frontend) + Groq LLaMA (LLM) + Redis (session memory).

---

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and set GROQ_API_KEY (get one free at console.groq.com)

# 4. Start Redis (required for session memory)
docker compose up -d redis

# 5. Start backend
uvicorn backend.main:app --reload --port 8000

# 6. Start frontend (separate terminal)
streamlit run frontend/app.py --server.port 8501
```

- **Frontend:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/api/v1/health

---

## How Data Works — Plain English

This is the most important section to understand before anything else.

### The core question: Does the AI see ALL your data for every message?

**No.** The system is designed to send only the data that is actually relevant to your question. Here is exactly how that works.

---

### Example: You ask "Why am I making a loss?"

**Step 1 — Your message is received.**

You type: `"Why am I making a loss?"` and select PORTFOLIO_002 (Priya Patel).

---

**Step 2 — A small, fast AI reads your question first (the Router).**

Before the main AI even sees your message, a lightweight model (`llama-3.1-8b-instant`) reads your question and decides: *what data do I need to answer this?*

For a loss-related question it will output something like:

```json
{
  "funds": { "ids": [], "fields": ["basic", "returns"] },
  "stocks": ["HDFCBANK", "ICICIBANK", "SBIN"],
  "sectors": ["BANKING"],
  "market": ["indices", "breadth"],
  "news": ["banking"],
  "reasoning": "User asking about portfolio loss — need banking stocks, sector performance, and banking news"
}
```

The router does NOT guess randomly. It looks at keywords in your question:

- "loss" / "down" / "red" → needs stock price changes and portfolio P&L
- "why" → needs news and causal context
- Portfolio is banking-heavy → focuses on banking stocks and sector

---

**Step 3 — Data is filtered (the Extractor).**

The system holds ~205 KB of JSON data files. Instead of dumping all of it into the AI prompt, only the slices matching the router's decision are pulled out.

For the loss example above, the extractor produces roughly **4–6 KB** of JSON:

```json
{
  "stocks": {
    "HDFCBANK": { "name": "HDFC Bank", "price": 1623.45, "change_percent": -3.51, "sector": "BANKING" },
    "ICICIBANK": { "name": "ICICI Bank", "price": 985.20, "change_percent": -2.14, "sector": "BANKING" },
    "SBIN":      { "name": "State Bank of India", "price": 789.30, "change_percent": -1.89, "sector": "BANKING" }
  },
  "sectors": {
    "BANKING": { "change_percent": -2.73, "sentiment": "bearish", "key_drivers": ["RBI hawkish stance", "Credit growth slowdown"] }
  },
  "market": {
    "indices": {
      "SENSEX": { "value": 72145.30, "change_percent": -1.24, "sentiment": "bearish" },
      "NIFTY50": { "value": 21890.45, "change_percent": -1.18, "sentiment": "bearish" }
    }
  },
  "news": [
    { "headline": "RBI signals tighter liquidity, repo rate unchanged but hawkish tone", "sentiment": "negative", "scope": "banking" },
    { "headline": "HDFC Bank Q3 results: NIM compression weighs on profit", "sentiment": "negative", "scope": "banking" }
  ],
  "portfolio": {
    "portfolio_id": "PORTFOLIO_002",
    "owner": "Priya Patel",
    "holdings": [
      { "symbol": "HDFCBANK", "units": 150, "avg_buy_price": 1685.00 },
      { "symbol": "ICICIBANK", "units": 200, "avg_buy_price": 1020.00 }
    ]
  },
  "portfolio_insights": {
    "day_pnl_rupees": -57390,
    "day_pnl_percent": -2.73,
    "sector_allocation": { "BANKING": 91.58 },
    "concentration_risk": "CRITICAL — 91.58% in Banking + Financial Services"
  },
  "relevant_news": [
    "RBI hawkish stance is directly impacting your HDFC Bank and ICICI Bank holdings"
  ]
}
```

This — and only this — goes to the reasoning AI. The rest of the dataset (IT stocks, pharma news, unrelated mutual funds, etc.) is **never sent**.

---

**Step 4 — The main AI builds and streams the answer.**

The reasoning model (`llama-3.3-70b-versatile`) receives:

```
[System prompt]
You are a financial advisor. Respond in this exact structure:
## Key Insights
## Causal Chain
## Holdings Mentioned
## Recommendations

[Last 5 conversation turns from memory]

[User message]
Data Context (filtered for this query):
{ ...the 4-6 KB JSON above... }

User Question: Why am I making a loss?
Using the provided data, explain the causal chain and provide your analysis.
```

The model streams its response token by token — you see words appear in real time, like ChatGPT.

---

**Step 5 — What you see.**

```
## Key Insights
- Your portfolio is down ₹57,390 (−2.73%) today
- 91.58% of your holdings are in Banking — extreme concentration risk
- RBI's hawkish tone triggered a sector-wide selloff

## Causal Chain
Market News → Sector Impact → Stock → Portfolio
- Market news: RBI signals tighter liquidity conditions
- Sector impact: Banking sector fell −2.73% broadly
- Stock impact: HDFC Bank −3.51%, ICICI Bank −2.14%
- Portfolio impact: ₹57,390 loss — your 91% banking exposure amplified the move

## Holdings Mentioned
- HDFC Bank (Banking): −3.51% today, largest drag on your portfolio

## Recommendations
1. Reduce banking concentration below 40% over the next 2–3 months
2. Add IT or FMCG stocks to diversify across uncorrelated sectors
3. Consider a Flexi Cap mutual fund to spread risk automatically
```

---

### Summary: What data is sent for common questions

| Your Question | Data the AI Receives |
| --- | --- |
| "Why am I making a loss?" | Your portfolio, banking stocks (price/change), sector P&L, banking news |
| "How is TCS performing?" | TCS stock data, IT sector performance, IT-related news |
| "What is my sector allocation?" | Your portfolio holdings, sector mapping only |
| "Compare my mutual funds' returns" | Only the specific fund IDs in your portfolio + their 1y/3y/5y returns |
| "Is the market bullish or bearish today?" | SENSEX/NIFTY indices, market breadth — no stock-level data unless needed |
| "What happened to pharma stocks?" | Pharma stocks, pharma sector data, pharma news only |

The router decides the list dynamically based on your words. It never sends all 205 KB.

---

### Does the AI see ALL the data or only relevant data?

**Only relevant data is sent — never all of it.** Here is the exact code path that proves it:

| Code line | What it does |
| --- | --- |
| `load_all_data()` | All ~205 KB of JSON is loaded into **server memory only** |
| `router.route_query(query)` | A fast AI reads your question and decides which stocks/sectors/news are needed |
| `extractor.extract(routing_decision, data)` | Only the matching slices are pulled out → `filtered_data_json` (~3–8 KB) |
| `_build_reasoner_prompt(filtered_data=filtered_data_json)` | **Only this filtered JSON** is put into the LLM prompt — nothing else |

The full 205 KB never leaves the server. Groq (the LLM) only ever receives the 3–8 KB slice relevant to your question.

You can verify this yourself in the server terminal — every query prints:

```
[Router] Routing decision: {"stocks": ["HDFCBANK", "ICICIBANK"], "sectors": ["BANKING"], ...}
[Extractor] Filtered data size: 4821 chars
```

That number (`4821 chars`) is what actually went to the AI — not the full dataset.

---

### What data is NEVER sent

- **API keys** — stored server-side only, never in any message
- **Unrelated stocks** — if you ask about pharma, banking stocks are excluded
- **Full historical data** — only the specific time slices needed (e.g., 7-day if asked)
- **Other users' portfolios** — each session is isolated by `session_id`
- **System internals** — Redis credentials, database URLs, backend config

---

## Architecture Overview

```
Browser (Streamlit)
    │
    │  HTTP / SSE (Server-Sent Events)
    ▼
FastAPI Backend (port 8000)
    │
    ├── POST /api/v1/chat/stream  ─── main chat endpoint (SSE streaming)
    ├── POST /api/v1/chat         ─── non-streaming fallback
    ├── POST /api/v1/chat/title   ─── auto-generate session title
    └── GET  /api/v1/portfolios   ─── portfolio list
    │
    ├── AdvisorAgent              ─── orchestrator (Router → Extractor → Reasoner)
    │     ├── DataRouter          ─── fast LLM classifies what data is needed
    │     ├── DataExtractor       ─── filters JSON data to minimal context
    │     └── GroqClient          ─── streams tokens from Groq API
    │
    ├── Redis                     ─── session history + response cache
    └── data/                     ─── mock JSON datasets
```

---

## Complete Query Processing Flow

This section traces exactly what happens when a user types a question, step by step.

---

### Step 1 — User submits query in the frontend

**File:** [frontend/app.py](frontend/app.py) → `handle_input()`

```
User types: "What are the risks of my portfolio?"
```

1. The message is appended to the current session's message list in `st.session_state`.
2. The user bubble renders immediately (before any backend call).
3. An assistant bubble opens with `_Thinking…_` placeholder.
4. `stream_chat()` is called — this opens an HTTP SSE connection to `/api/v1/chat/stream`.

**Key design:** The user sees their own message the instant they press Enter. The "Thinking…" state appears in the assistant bubble right away, eliminating the perceived blank gap.

---

### Step 2 — Frontend streams tokens via SSE

**File:** [frontend/utils/api_client.py](frontend/utils/api_client.py) → `stream_chat()`

```
POST /api/v1/chat/stream
Body: { session_id, message, portfolio_id, settings? }
```

- `settings` may override: `groq_model`, `groq_temperature`, `groq_max_tokens`.
- **API keys are never sent from the frontend** — only safe inference parameters.
- The client holds the SSE connection open and yields decoded tokens as they arrive.
- Each token from the server is **JSON-encoded** (e.g., `"\n"` → `"\"\\n\""`) so that newline characters survive SSE's line-based transport without being stripped.

```python
# Server sends:    event: token
#                  data: "## Key Insights\n"
# Client decodes:  json.loads(data) → "## Key Insights\n"  ✓ newline preserved
```

---

### Step 3 — Backend checks response cache (Redis)

**File:** [backend/routers/chat.py](backend/routers/chat.py) → `chat_stream()` → `_get_cached()`

Cache key = `md5(portfolio_id + normalized_query)`
Cache TTL = 10 minutes
Store = Redis (falls back to in-process dict if Redis is unreachable)

```
Cache HIT  → stream cached response immediately, no LLM call
Cache MISS → proceed to Step 4
```

This means repeated identical queries (e.g., refreshing the same analysis) return instantly without consuming Groq API quota.

---

### Step 4 — Router LLM classifies what data is needed

**File:** [backend/agent/router.py](backend/agent/router.py) → `DataRouter.route_query()`

**Model used:** `llama-3.1-8b-instant` (fast, cheap — router-only)

The router receives the raw user query and returns a structured JSON routing decision:

```json
{
  "funds": { "ids": ["MF001", "MF004"], "fields": ["basic", "returns"] },
  "stocks": ["HDFCBANK", "TCS", "INFY"],
  "sectors": ["BANKING", "IT"],
  "market": ["indices", "breadth"],
  "news": ["banking", "it"],
  "reasoning": "User asked about portfolio risk with banking focus"
}
```

**Why this matters:** The full dataset is ~205 KB of JSON. Sending everything to the reasoning LLM wastes tokens (cost + quality). The router reduces context to only what's relevant — typically 3–8 KB.

**Implementation detail:** Uses `AsyncGroq` (non-blocking) so the event loop is never blocked during the router call. Falls back to a sensible default routing if the router LLM fails.

---

### Step 5 — DataExtractor filters the dataset

**File:** [backend/agent/data_extractor.py](backend/agent/data_extractor.py) → `DataExtractor.extract()`

Uses the routing decision to pull exactly the right slices from the loaded JSON data:

```
All data (market + news + portfolios + mutual_funds + historical + sector_mapping)
     │
     │  routing decision
     ▼
Filtered data JSON (only relevant stocks, sectors, news articles, fund details)
```

Example: for a banking-risk query, the extractor returns:
- HDFC Bank, ICICI Bank, SBI price/change data
- Banking sector details
- RBI-related news articles
- User's banking holdings from their portfolio

---

### Step 6 — Portfolio analytics computed

**File:** [backend/agent/agent.py](backend/agent/agent.py) → `stream_answer()` + [backend/intelligence/portfolio_analytics.py](backend/intelligence/portfolio_analytics.py)

If a `portfolio_id` is provided:

| Metric | Description |
|--------|-------------|
| `day_pnl` | Rupee and % P&L for the current day |
| `sector_allocation` | % weight per sector |
| `concentration_risk` | Warning if any single stock/sector > threshold |
| `relevant_news` | News articles mapped to the user's actual holdings |

These computed values are merged into the filtered data before building the LLM prompt.

---

### Step 7 — Prompt built for the reasoning LLM

**File:** [backend/agent/agent.py](backend/agent/agent.py) → `_build_reasoner_prompt()`

The prompt has three parts:

**System prompt** — hard-wired Markdown structure instructions:
```
You are a financial advisor analyzing Indian markets.
Respond strictly in this structure:
## Key Insights
- ...
## Causal Chain
**Market News → Sector Impact → Stock → Portfolio**
- Market news: ...
- Sector impact: ...
...
## Holdings Mentioned
- Stock (Sector): note
## Recommendations
1. ...
```

Naming rules are explicit: "Write HDFC Bank not HDFCBANK", "Write Information Technology not INFORMATION_TECHNOLOGY" etc. This prevents the LLM from emitting raw data codes.

**Conversation history** — last 5 turns (10 messages) from Redis, so follow-up questions have context.

**User message** — the query plus the filtered data JSON:
```
Data Context (filtered for this query):
{ ...3-8 KB of relevant JSON... }

User Question: What are the risks of my portfolio?
Using the provided data, explain the causal chain and provide your analysis.
```

---

### Step 8 — Reasoning LLM streams the response

**File:** [backend/groq_client/streaming.py](backend/groq_client/streaming.py) → `stream_openai_compatible()`

**Model used:** `llama-3.3-70b-versatile` (full reasoning model)

- Calls `https://api.groq.com/openai/v1/chat/completions` with `stream: true`.
- Handles rate limiting (429) with exponential backoff: 2s, 4s, 8s, 16s, 32s.
- Yields each token as it arrives from Groq.
- **Token transport:** each token is `json.dumps()`-encoded in the SSE `data:` field so newline tokens (`\n`) are not eaten by SSE's line-based protocol.

```
Groq streams: "## " → " Key" → " Insights" → "\n" → "- " → "HDFC" → " Bank" → ...
     ↓
SSE events:   data: "## "   data: " Key"   data: " Insights"   data: "\n"   ...
     ↓
Frontend:     accumulates → placeholder.markdown(accumulated + "▌")
```

---

### Step 9 — Session memory saved

**File:** [backend/memory/conversation_manager.py](backend/memory/conversation_manager.py)

After streaming completes:
1. User message and assistant response are appended to Redis (key: `session:{session_id}`).
2. History is trimmed to the last 5 turns to keep prompt size bounded.
3. Formatted response is saved to the response cache (key: `resp:{cache_key}`).

```
Redis keys written per query:
  session:{uuid}  →  [{"role":"user","content":"..."},{"role":"assistant","content":"..."},...]
  resp:{md5hash}  →  "## Key Insights\n- ..."  (10-min TTL)
```

---

### Step 10 — Session title auto-generated

**File:** [backend/routers/chat.py](backend/routers/chat.py) → `generate_title()`
**File:** [frontend/app.py](frontend/app.py) → `handle_input()` (called after first message only)

On the user's **first** message in a new session:

```
POST /api/v1/chat/title
Body: { session_id, message }
```

Backend calls `llama-3.1-8b-instant` (fast model) with:
```
System: "Generate a concise 4-6 word title. Return ONLY the title text."
User:   "What are the risks of my portfolio?"
```

Returns: `"Portfolio Risk Analysis"` → stored in Redis (`title:{session_id}`) → displayed in the sidebar.

---

## Data Files

| File | Contents | Size |
|------|----------|------|
| `data/market_data.json` | 40+ stocks, 5 indices, 10 sectors with live-like prices | ~80 KB |
| `data/news_data.json` | 25 tagged news articles with sentiment and entity links | ~30 KB |
| `data/portfolios.json` | 3 sample portfolios (Diversified / Sector-heavy / Conservative) | ~20 KB |
| `data/mutual_funds.json` | 12 fund schemes with NAV, holdings, returns | ~25 KB |
| `data/historical_data.json` | 7-day index/stock history, FII/DII flows | ~40 KB |
| `data/sector_mapping.json` | Macro correlations, sector characteristics | ~10 KB |

**Total: ~205 KB.** Per query, only 3–8 KB is extracted and sent to the AI.

---

## Portfolio Profiles

### PORTFOLIO_001 — Diversified (Rahul Sharma)
- **Mix:** 38% stocks, 62% mutual funds
- **Day P&L:** −0.44% (₹−12,785)
- **Concentration risk:** None (max single stock: TCS at 7.17%)
- **Sectors:** IT, FMCG, Banking, Energy, Pharma

### PORTFOLIO_002 — Sector-Concentrated (Priya Patel)
- **Mix:** 91% stocks (all Banking/FS), 9% mutual funds
- **Day P&L:** −2.73% (₹−57,390)
- **Concentration risk:** CRITICAL — 91.58% in Banking + Financial Services
- **Trigger:** RBI hawkish stance → HDFC Bank −3.51% (22.62% of portfolio)

### PORTFOLIO_003 — Conservative (Arun Krishnamurthy)
- **Mix:** 21% stocks, 79% mutual funds (34% debt)
- **Day P&L:** −0.04% (₹−1,758)
- **Concentration risk:** None
- **Holdings:** Defensive (ITC, HUL) + large debt fund allocation

---

## API Reference

### `POST /api/v1/chat/stream` — Main streaming endpoint

```json
{
  "session_id": "uuid-string",
  "message": "What are the risks of my portfolio?",
  "portfolio_id": "PORTFOLIO_001",
  "settings": {
    "groq_model": "llama-3.3-70b-versatile",
    "groq_temperature": 0.2,
    "groq_max_tokens": 512
  }
}
```

> **Security note:** `settings` accepts ONLY `groq_model`, `groq_temperature`, `groq_max_tokens`.
> API keys, database URLs, and Redis credentials are **never** accepted in request bodies.

Returns: `text/event-stream` (SSE) with events:
- `event: token` → `data: "<JSON-encoded token>"`
- `event: error` → `data: "<user-friendly error message>"`
- `event: final` → `data: "<full formatted response>"`
- `event: done`  → `data: "[DONE]"`

### `POST /api/v1/chat` — Non-streaming fallback

Same request body. Returns:
```json
{ "answer": "## Key Insights\n- ..." }
```

### `POST /api/v1/chat/title` — Generate session title

```json
{ "session_id": "uuid", "message": "first user message" }
```

Returns: `{ "title": "Portfolio Risk Analysis" }`

### `GET /api/v1/portfolios` — List portfolios

Returns: `[{ "portfolio_id": "PORTFOLIO_001", "name": "Rahul Sharma - Diversified" }, ...]`

---

## Redis Key Schema

| Key pattern | Content | TTL |
|-------------|---------|-----|
| `session:{uuid}` | JSON array of conversation turns | `SESSION_TTL_SECONDS` (default 1h) |
| `resp:{md5}` | Full LLM response for a query | 10 minutes |
| `title:{uuid}` | Auto-generated session title | `SESSION_TTL_SECONDS` |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | From console.groq.com |
| `GROQ_MODEL` | No | Default: `llama-3.3-70b-versatile` |
| `GROQ_ROUTER_MODEL` | No | Default: `llama-3.1-8b-instant` |
| `GROQ_MAX_TOKENS` | No | Default: `512` |
| `GROQ_TEMPERATURE` | No | Default: `0.2` |
| `REDIS_URL` | No | Default: `redis://localhost:6379` |
| `SESSION_TTL_SECONDS` | No | Default: `3600` |
| `API_BASE_URL` | No | Default: `http://localhost:8000` |

> **Never commit `GROQ_API_KEY` to git.** The `.gitignore` already excludes `.env`.

---

## Project Structure

```
Financial-Advisor/
├── backend/
│   ├── agent/
│   │   ├── agent.py            # Orchestrator: Router → Extractor → Reasoner
│   │   ├── router.py           # Fast LLM: classifies data needs (AsyncGroq)
│   │   ├── data_extractor.py   # Filters dataset to minimal context
│   │   ├── context_selector.py # Legacy context builder
│   │   └── prompt_builder.py   # System prompt template
│   ├── groq_client/
│   │   ├── client.py           # GroqClient wrapper with retry logic
│   │   └── streaming.py        # SSE stream reader + 429 backoff
│   ├── intelligence/
│   │   ├── data_loader.py      # Loads JSON data files
│   │   ├── portfolio_analytics.py  # P&L, sector allocation, concentration risk
│   │   ├── market_intelligence.py  # Index/breadth analysis
│   │   └── news_processor.py   # News → portfolio impact mapping
│   ├── memory/
│   │   ├── session_manager.py  # Redis + InMemory stores (session, cache, title)
│   │   └── conversation_manager.py  # Load/append conversation history
│   ├── models/
│   │   └── request_models.py   # ChatRequest, SafeSettings (no API keys)
│   ├── routers/
│   │   ├── chat.py             # /chat, /chat/stream, /chat/title endpoints
│   │   ├── portfolio.py        # /portfolios endpoints
│   │   └── health.py           # /health endpoint
│   ├── config.py               # Settings loaded from .env
│   ├── dependencies.py         # FastAPI dependency injection
│   └── main.py                 # FastAPI app factory
├── frontend/
│   ├── app.py                  # ChatGPT-like Streamlit UI (multi-session)
│   ├── components/
│   │   ├── chat_window.py      # Message history renderer
│   │   ├── portfolio_panel.py  # Sidebar portfolio widget
│   │   └── market_snapshot.py  # Market sentiment widget
│   └── utils/
│       ├── api_client.py       # HTTP + SSE client (stream_chat, generate_title)
│       └── state.py            # Multi-session Streamlit state management
├── data/                       # Mock JSON datasets
├── scripts/                    # DB init/seed utilities
├── docker-compose.yml          # Redis + Postgres services
├── requirements.txt
└── .env                        # Local secrets (not committed)
```

---

## Extending the System

### Add a new portfolio
Edit `data/portfolios.json` — follow the existing schema. Restart the backend.

### Change the LLM response format
Edit `_build_reasoner_prompt()` in [backend/agent/agent.py](backend/agent/agent.py). The system prompt controls the Markdown structure.

### Add a new data source

1. Add a loader in [backend/intelligence/data_loader.py](backend/intelligence/data_loader.py)
2. Add routing keys in [backend/agent/router.py](backend/agent/router.py) (ROUTER_PROMPT)
3. Add extraction logic in [backend/agent/data_extractor.py](backend/agent/data_extractor.py)

### Increase response cache TTL
Change `RESPONSE_CACHE_TTL` in [backend/memory/session_manager.py](backend/memory/session_manager.py) (default 600 seconds).
