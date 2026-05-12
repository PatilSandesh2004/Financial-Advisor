# 📊 Financial Advisor – Complete Guide

A **lightweight, intelligent financial advisor** that explains Indian portfolio movements through causal reasoning: **Macro News → Sector Trend → Stock Impact → Portfolio Impact**

Built with **FastAPI** (backend) + **HTML/CSS/JS** (frontend) + **Groq LLaMA** (AI reasoning) + **Redis** (session memory) + **Langfuse** (observability).

---

## 🚀 Quick Setup (5 Minutes)

### **Step 1: Prepare Your Environment**

```bash
# Navigate to project directory
cd /home/sandeshpatil/Downloads/Financial-Advisor/Financial-Advisor

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate
```

### **Step 2: Install Dependencies**

```bash
pip install -r requirements.txt
```

**Required packages:** fastapi, uvicorn, langfuse, groq, redis, httpx, python-dotenv, pydantic

### **Step 3: Configure Your Environment**

Create a `.env` file in the project root with:

```env
# Groq API (get free key from https://console.groq.com)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_ROUTER_MODEL=llama-3.1-8b-instant

# Langfuse Observability (optional, for trace viewing)
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_BASE_URL=https://cloud.langfuse.com

# Redis (for session storage)
REDIS_URL=redis://localhost:6379

# Backend configuration
DATABASE_URL=sqlite:///portfolio.db
API_BASE_URL=http://127.0.0.1:8050
LOG_LEVEL=INFO
```

### **Step 4: Start Redis (Session Storage)**

```bash
# Option 1: Using Docker
docker run -d -p 6379:6379 redis:alpine

# Option 2: If you have Redis installed locally
redis-server
```

### **Step 5: Start Backend**

```bash
# In terminal 1
PYTHONPATH=/home/sandeshpatil/Downloads/Financial-Advisor/Financial-Advisor \
  python3 -m uvicorn backend.main:app --port 8050 --host 127.0.0.1 --reload
```

✅ Backend ready at: http://localhost:8050

### **Step 6: Start Frontend**

```bash
# In terminal 2
cd /home/sandeshpatil/Downloads/Financial-Advisor/Financial-Advisor/UI
python3 -m http.server 8080
```

✅ Frontend ready at: http://localhost:8080

---

## 📌 What This Project Does

### **For Users:**

You upload your portfolio (stocks, percentages, entry prices). Then ask questions naturally:

- *"Why did my portfolio drop 2% today?"*
- *"How will rising interest rates affect my tech stocks?"*
- *"Which sectors should I increase?"*

The advisor:
1. **Understands** your question and figures out what financial data you need
2. **Extracts** relevant holdings, sectors, and historical data from your portfolio
3. **Reasons** with AI using market data to explain the answer
4. **Returns** an explanation with the causal chain

### **For Developers:**

A **production-ready template** for building AI-powered financial tools showing:
- Multi-stage LLM reasoning pipeline (router → extractor → reasoner)
- Server-Sent Events (SSE) for real-time token streaming
- Session-based portfolio memory with Redis
- Observability & tracing with Langfuse
- Clean separation: backend logic ↔ frontend UI

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interaction                      │
│                  (Streamlit Frontend)                    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ HTTP + SSE
                  ↓
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (8050)                      │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  /api/v1/chat Endpoint (Streaming)                │ │
│  │  ↓ Session Management (Redis)                     │ │
│  │  ↓ Create Parent Trace (Langfuse)                │ │
│  │  ↓ Call AdvisorAgent                            │ │
│  │  ↓ Stream tokens back to frontend               │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  AdvisorAgent (3-Stage Pipeline)                  │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │ Stage 1: Router                           │ │ │
│  │  │ (What kind of question is this?)          │ │ │
│  │  │ Uses: llama-3.1-8b-instant (fast)        │ │ │
│  │  └─────────────────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │ Stage 2: Extractor                        │ │ │
│  │  │ (Extract relevant portfolio data)         │ │ │
│  │  │ Uses: llama-3.3-70b-versatile (powerful) │ │ │
│  │  └─────────────────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │ Stage 3: Reasoner                         │ │ │
│  │  │ (Generate explanation with data)          │ │ │
│  │  │ Uses: llama-3.3-70b-versatile (powerful) │ │ │
│  │  └─────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
└────────┬──────────────────┬──────────────────┬──────────┘
         │                  │                  │
    ┌────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
    │   Groq    │   │    Redis    │   │  Langfuse  │
    │   LLM     │   │   Session   │   │   Traces   │
    │ (API)     │   │   Storage   │   │  (Cloud)   │
    └───────────┘   └─────────────┘   └────────────┘
```

---

## 🔄 How a Query Gets Processed (Step-by-Step)

### **User Message: "Why did my portfolio drop 2% today?"**

```
Step 1: Message Arrives at Backend
├─ HTTP POST /api/v1/chat
├─ Session ID retrieved from Redis
├─ Create parent trace in Langfuse (for observability)
└─ ✅ Now being tracked: trace_id = "abc123..."

Step 2: Router Stage (Fast Classification)
├─ Model: llama-3.1-8b-instant
├─ Question: "Classify: portfolio performance question"
├─ Output: "PORTFOLIO_ANALYSIS" category
├─ Time: ~200ms
└─ ✅ Logged to trace

Step 3: Extractor Stage (Data Gathering)
├─ Model: llama-3.3-70b-versatile
├─ Prompt includes: User's portfolio, question category
├─ Output: List of relevant sectors/stocks to analyze
├─ Time: ~500ms
├─ Retrieves from Redis:
│   ├─ Portfolio holdings (saved in session)
│   ├─ Sector classifications
│   └─ Recent price data
└─ ✅ Data span logged to trace

Step 4: Reasoner Stage (Answer Generation)
├─ Model: llama-3.3-70b-versatile
├─ Prompt built with:
│   ├─ Full question
│   ├─ Extracted relevant stocks/sectors
│   ├─ User's portfolio positions
│   └─ Market context (if available)
├─ Streams tokens one-by-one using SSE
├─ Time: ~1-2 seconds (depends on answer length)
├─ Each token wrapped: {"type": "token", "content": "word"}
└─ ✅ Generation span logged to trace

Step 5: Response Complete
├─ All tokens streamed to frontend
├─ Trace finalized in memory
├─ Trace synced to Langfuse cloud (~2-5 seconds)
└─ ✅ Complete trace visible in dashboard

Frontend sees:
"Your portfolio dropped because Tech sector fell 3%,
affecting your AAPL/MSFT holdings..."
```

---

## 💾 Key Components Explained

### **Backend Structure**

| Component | Purpose |
|-----------|---------|
| `backend/main.py` | FastAPI app initialization, CORS, routes setup |
| `backend/routers/chat.py` | POST `/api/v1/chat` endpoint with streaming |
| `backend/agent/agent.py` | 3-stage reasoning pipeline (Router→Extractor→Reasoner) |
| `backend/observability/langfuse_client.py` | Singleton Langfuse client initialization |
| `backend/observability/tracing.py` | Trace/span wrapper API with SDK calls |
| `backend/session/redis_manager.py` | Session storage and retrieval from Redis |

### **Frontend Structure**

| Component | Purpose |
|-----------|---------|
| `frontend/app.py` | Main Streamlit UI, manages chat interface |
| `frontend/styles.py` | CSS styling and visual configuration |

### **Configuration**

| File | Purpose |
|------|---------|
| `.env` | API keys, URLs, environment settings |
| `requirements.txt` | Python dependencies |

---

## 🔐 Environment Variables Explained

### **Groq Configuration**

```env
GROQ_API_KEY=your_key_here
```
- Get free API key: https://console.groq.com
- Used for all LLM calls (routing, extraction, reasoning)

```env
GROQ_MODEL=llama-3.3-70b-versatile
```
- Main model for complex reasoning (extraction, generation)
- Larger, slower, more capable

```env
GROQ_ROUTER_MODEL=llama-3.1-8b-instant
```
- Fast model for simple classification (stage 1)
- Smaller, faster, good for categorization

### **Langfuse Configuration (Optional)**

```env
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```
- For tracing & observability (debugging, performance analysis)
- Optional: if keys missing, tracing gracefully disables
- Account: https://langfuse.com (free tier available)

### **Redis Configuration**

```env
REDIS_URL=redis://localhost:6379
```
- Session storage location
- Must be running before backend starts

### **System Configuration**

```env
API_BASE_URL=http://127.0.0.1:8050
DATABASE_URL=sqlite:///portfolio.db
LOG_LEVEL=INFO
```
- API_BASE_URL: Backend address (used by frontend)
- LOG_LEVEL: Verbosity (DEBUG, INFO, WARNING, ERROR)

---

## 🔍 Monitoring & Debugging

### **View Live Traces**

1. Get your Langfuse keys from: https://cloud.langfuse.com
2. Set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in `.env`
3. Send a message through frontend
4. Traces appear in Langfuse dashboard within 2-5 seconds
5. Each trace shows:
   - Parent trace: entire chat request
   - Stage 1 span: router decision
   - Stage 2 span: data extraction
   - Stage 3 span: answer generation
   - Token counts & latencies for each

### **Backend Logs**

```
[CHAT STREAM] User message: "..."
[AGENT STEP 1] Routing decision: PORTFOLIO_ANALYSIS
[AGENT STEP 2] Extracted stocks: [...]
[AGENT STEP 3] Generating answer...
[TRACE] Trace created successfully (ID: abc123...)
```

### **Common Issues**

| Issue | Cause | Fix |
|-------|-------|-----|
| 404 Backend not reachable | Wrong working directory or PYTHONPATH | Set `PYTHONPATH=/full/path/to/Financial-Advisor/Financial-Advisor` |
| Redis connection refused | Redis not running | Start Redis: `docker run -d -p 6379:6379 redis:alpine` |
| GROQ_API_KEY error | Missing or invalid key | Get from https://console.groq.com |
| Traces not appearing | Langfuse credentials missing | Set PUBLIC/SECRET keys, wait 2-5 seconds |
| Streamlit not connecting | Frontend can't reach backend | Ensure backend running on 8050, check `API_BASE_URL` in `.env` |

---

## 📁 Project Structure

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed file organization.

---

## 🎯 Feature Explanation

### **Multi-Stage Reasoning**

Instead of asking the LLM one big question, we break it into stages:

1. **Router** (fast, small model): "Is this a portfolio question or general finance?"
2. **Extractor** (powerful, large model): "What stocks from the portfolio matter?"
3. **Reasoner** (powerful, large model): "Generate a detailed answer"

**Benefit:** Cheaper, faster, more accurate answers.

### **Real-Time Streaming**

Answer tokens appear word-by-word (like ChatGPT) using Server-Sent Events (SSE):

```
Browser → Backend (streaming)
          Backend to Groq LLM
          LLM returns tokens
          Backend streams to frontend
          Frontend displays token-by-token
```

### **Session Memory**

Your portfolio stays in memory for the session:
- Upload portfolio once
- Ask multiple questions
- Each question uses same portfolio data
- Session expires after 1 hour (TTL=3600s)

### **Observability with Langfuse**

Every message is traced:
- Parent trace: entire request
- Child spans: each pipeline stage
- Metadata: session ID, portfolio ID, query text
- Metrics: token counts, latencies
- Purpose: Debugging, performance analysis, cost tracking

---

## 🔍 Langfuse Observability Setup & Usage

Langfuse is an open-source LLM observability platform integrated into our system. Every AI request is automatically tracked, allowing you to:
- **Monitor costs** - See exactly how much each query costs
- **Debug issues** - Trace exactly what went wrong and where
- **Optimize performance** - Identify slow stages and cache hits
- **Track usage** - Understand which questions are asked most

### **Setup: Get Langfuse Credentials**

**Step 1: Create Account**
- Go to https://cloud.langfuse.com
- Sign up (free tier available)
- Create a new project

**Step 2: Get API Keys**
- Click "Settings" in top-right
- Navigate to "API Keys"
- Copy your:
  - **Public Key** → `LANGFUSE_PUBLIC_KEY`
  - **Secret Key** → `LANGFUSE_SECRET_KEY`
  - Base URL → `https://cloud.langfuse.com`

**Step 3: Update .env**
```env
LANGFUSE_PUBLIC_KEY=pk_prod_your_public_key_here
LANGFUSE_SECRET_KEY=sk_prod_your_secret_key_here
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

**Step 4: Restart Backend**
```bash
# Stop backend (Ctrl+C)
# Then restart with:
PYTHONPATH=/home/sandeshpatil/Downloads/Financial-Advisor/Financial-Advisor \
  python3 -m uvicorn backend.main:app --port 8050 --host 127.0.0.1 --reload
```

**That's it!** Traces now send automatically.

### **Viewing Your Traces**

**1. Dashboard Overview**
```
Go to: https://cloud.langfuse.com/dashboard
├─ Traces tab - See all requests made
├─ Analytics - View costs, latencies, errors
└─ Documentation - Langfuse guides
```

**2. Filter Traces by Session**
```
├─ Date range
├─ Session ID (find by user)
├─ Status (success/error)
├─ Model (llama-3.1 vs llama-3.3)
└─ Duration (fast/slow queries)
```

**3. Click on a Trace to See Details**

```
Parent Trace View:
├─ Duration: 2600ms total
├─ Tokens: 1787 input + 194 output
├─ Cost: $0.013
├─ Status: Success
├─ Metadata:
│  ├─ session_id: user-123
│  ├─ portfolio_id: portfolio-456
│  ├─ query: "Why did portfolio drop?"
│  └─ endpoint: /api/v1/chat
│
└─ Child Spans:
   ├─ Span: route_classification (250ms, $0.0003)
   ├─ Span: data_extraction (750ms, $0.0045)
   └─ Span: answer_generation (1800ms, $0.0085)
```

**4. Click on Any Span to See Details**

```
Span: answer_generation
├─ Model: llama-3.3-70b-versatile
├─ Input:
│  ├─ Question: "Why did portfolio drop?"
│  ├─ Category: PORTFOLIO_ANALYSIS
│  ├─ Extracted data: [AXIS, Banking sector, ...]
│  └─ Full portfolio: {AAPL: 50, INFY: 100, ...}
├─ Output: 182 tokens (full answer text)
├─ Tokens:
│  ├─ Input: 1250 tokens
│  ├─ Output: 182 tokens
│  └─ Cost: $0.0085
├─ Latency:
│  ├─ Total: 1800ms
│  ├─ First token: 450ms
│  ├─ Per token: 9.9ms average
│  └─ Status: COMPLETED
```

### **Understanding Costs**

Each request makes **3 LLM calls**, costing different amounts:

```
Stage 1: Router (Fast model, 8B parameters)
├─ Model: llama-3.1-8b-instant
├─ Input: ~50 tokens (your question)
├─ Output: ~10 tokens (category name)
├─ Cost: ~$0.0003 per request

Stage 2: Extractor (Powerful model, 70B parameters)
├─ Model: llama-3.3-70b-versatile
├─ Input: ~450 tokens (question + portfolio)
├─ Output: ~300 tokens (relevant stocks)
├─ Cost: ~$0.0045 per request
├─ Cached? If yes → $0 (reuses 10-min cache)

Stage 3: Reasoner (Powerful model, 70B parameters)
├─ Model: llama-3.3-70b-versatile
├─ Input: ~1250 tokens (question + extracted + portfolio)
├─ Output: ~180 tokens (full answer)
├─ Cost: ~$0.0085 per request
├─ Cached? If yes → $0 (reuses 1-hour cache)
```

**Real Cost Comparison:**
```
Scenario 1: New question (all 3 stages)
├─ Router: $0.0003
├─ Extractor: $0.0045
├─ Reasoner: $0.0085
└─ Total: $0.0133

Scenario 2: Similar question (extraction cached, stage 2 skipped)
├─ Router: $0.0003
├─ Extractor: $0 (cached)
├─ Reasoner: $0.0085
└─ Total: $0.0088 (34% cheaper!)

Scenario 3: Exact same question (full response cached)
├─ Router: $0 (no API call needed)
├─ Extractor: $0 (no API call needed)
├─ Reasoner: $0 (no API call needed)
└─ Total: $0.0000 (100% free!)
```

### **Cost Analytics Dashboard**

Langfuse shows:
```
Last 7 Days:
├─ Total Requests: 156
├─ Total Cost: $1.87
├─ Average Cost: $0.012 per request
├─ Cache Hit Rate: 38% (cheaper!)
├─ Most Expensive Stage: Reasoner (65% of cost)
├─ Most Used Model: llama-3.3-70b (70% of cost)
└─ Projected Monthly: ~$56 (at current rate)
```

### **Error Tracking**

When something goes wrong, Langfuse captures it:

```
Example: Invalid Groq API Key
├─ Status: FAILED
├─ Error Stage: route_classification (Stage 1)
├─ Error Type: 401 Unauthorized
├─ Error Message: "Invalid API key for Groq"
├─ Time to Failure: 45ms
├─ Input: "Why did portfolio drop?"
├─ Output: None (failed before output)
│
Fix:
├─ Check GROQ_API_KEY in .env
├─ Verify key at https://console.groq.com
├─ Restart backend with new key
└─ Re-run request
```

### **Performance Optimization Tips**

Using Langfuse data to optimize:

```
1. Identify Slow Stages
   └─ If Stage 3 is slow → Reasoner model is slow
      └─ Reduce max_tokens in prompt
      └─ Or switch to faster model

2. Reduce Cache Misses
   └─ Low extraction cache hit? → Portfolio data is very different
      └─ Consider caching full responses for 24 hours instead of 1 hour

3. Monitor API Errors
   └─ High error rate on Stage 2? → Extractor is brittle
      └─ Improve prompt to be more robust

4. Cost Optimization
   └─ If cost is too high → Disable reasoner caching, enable 24-hour cache
      └─ Or route simpler questions to faster 8B model
```

### **Integration Details**

**What Langfuse tracks automatically:**
```
Every request:
├─ Parent trace with session_id, portfolio_id, query
├─ All 3 pipeline stages as child spans
├─ LLM model, input tokens, output tokens, latency
├─ Errors and exceptions
├─ Response success/failure status
├─ Cache hits/misses

Every trace:
├─ Syncs to cloud 2-5 seconds after request completes
├─ Becomes queryable in dashboard
├─ Included in analytics calculations
└─ Retained for 90 days (upgrade for longer)
```

**Files involved:**
```
backend/observability/langfuse_client.py
├─ Initializes Langfuse SDK on startup
├─ Creates singleton client instance
└─ Handles credentials from .env

backend/observability/tracing.py
├─ create_trace() - Start parent trace
├─ start_span() - Start stage span
├─ end_span() - End stage span with timing
├─ track_event() - Log intermediate events
└─ track_generation() - Track LLM calls

backend/routers/chat.py
├─ Creates trace at request start
├─ Passes trace to all components
└─ Finalizes trace at response end

backend/agent/agent.py
├─ Each stage (router, extractor, reasoner) creates span
├─ Logs input/output with metadata
└─ Langfuse auto-tracks all Groq LLM calls
```

---

## 💡 Example Workflow

### **1. User Uploads Portfolio**

```
Portfolio:
- AAPL: 30%, Entry: ₹3000
- INFY: 25%, Entry: ₹2500
- TCS: 20%, Entry: ₹2800
- Axis Bank: 25%, Entry: ₹800
```

→ Stored in Redis session (1 hour TTL)

### **2. User Asks Question**

```
"Axis Bank dropped 3%, why?"
```

→ Routed to backend, traced, processed through 3 stages

### **3. Backend Processes**

```
Stage 1: Router → "STOCK_PERFORMANCE_QUESTION"
Stage 2: Extractor → "Focus on Axis Bank, banking sector"
Stage 3: Reasoner → "Axis dropped because RBI hiked rates..."
```

→ Tokens streamed back one by one

### **4. User Sees**

```
"Axis Bank's 3% drop is driven by RBI's interest rate hike
announced this morning. Banks are sensitive to rate changes
as higher rates reduce loan demand. Your portfolio exposure
is 25% to Axis, so this impacts overall returns..."
```

---

## ❓ FAQ

**Q: Do I need to upload my portfolio every time?**  
A: No, it's stored for the session (1 hour). Close and reopen to reset.

**Q: Can I run this without Langfuse?**  
A: Yes! Langfuse is optional for observability. Without it, tracing gracefully disables.

**Q: What if I don't have a Groq API key?**  
A: Get a free one (with generous limits) at https://console.groq.com

**Q: How accurate are the explanations?**  
A: As good as the LLM's market knowledge + your portfolio data. Always verify with domain experts.

**Q: Can I use other LLMs instead of Groq?**  
A: Yes, modify `backend/agent/agent.py` to use OpenAI, Claude, etc.

---

## 🚨 Troubleshooting

### **Backend won't start**

```bash
# Check Python path
echo $PYTHONPATH

# Set it correctly
export PYTHONPATH=/home/sandeshpatil/Downloads/Financial-Advisor/Financial-Advisor

# Try again
python3 -m uvicorn backend.main:app --port 8050 --reload
```

### **UI not connecting to backend**

```bash
# Verify backend is running
curl http://127.0.0.1:8050/api/v1/health

# Check .env has correct API_BASE_URL
cat .env | grep API_BASE_URL

# Restart frontend
cd UI && python3 -m http.server 8080
```

### **Redis connection fails**

```bash
# Check if Redis is running
redis-cli ping

# Start Redis
docker run -d -p 6379:6379 redis:alpine

# Or on Mac/Linux with local install
redis-server
```

### **Traces not syncing to Langfuse**

```bash
# Check credentials in .env
cat .env | grep LANGFUSE

# Verify keys are valid at https://cloud.langfuse.com

# Wait 2-5 seconds (normal sync time)
# Check dashboard: https://cloud.langfuse.com/dashboard
```

---

## 📚 Next Steps

1. **Read** [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) for deep technical details
2. **Explore** [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for file organization
3. **Modify** `backend/agent/agent.py` to add custom logic
4. **Deploy** to production (see backend/main.py for production setup)

---

**Happy analyzing! 📈**
# Autonomous Financial Advisor

A  financial advisor that explains Indian portfolio movements through a causal chain:
**Macro News → Sector Trend → Stock Impact → Portfolio Impact**

Built with FastAPI (backend) + HTML/CSS/JS (frontend) + Groq LLaMA (LLM) + Redis (session memory).

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
cd UI
python3 -m http.server 8080
```

- **Frontend:** http://localhost:8080
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
    ├── POST /api/v1/chat           ─── main chat endpoint (SSE streaming)
    ├── POST /api/v1/chat/complete  ─── non-streaming fallback
    ├── POST /api/v1/chat/title     ─── auto-generate session title
    ├── POST /api/v1/router         ─── internal router decision endpoint
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
4. `stream_chat()` is called — this opens an HTTP SSE connection to `/api/v1/chat`.

**Key design:** The user sees their own message the instant they press Enter. The "Thinking…" state appears in the assistant bubble right away, eliminating the perceived blank gap.

---

### Step 2 — Frontend streams tokens via SSE

**File:** [frontend/utils/api_client.py](frontend/utils/api_client.py) → `stream_chat()`

```
POST /api/v1/chat
Body: { session_id, message, portfolio_id }
```

- **Only** `session_id`, `message`, and `portfolio_id` are sent from the frontend.
- API keys, database URLs, and other sensitive configuration must stay in the backend `.env` file.
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

### `POST /api/v1/chat` — Main streaming endpoint

```json
{
  "session_id": "uuid-string",
  "message": "What are the risks of my portfolio?",
  "portfolio_id": "PORTFOLIO_001"
}
```

> **Security note:** The chat endpoint accepts only `session_id`, `message`, and `portfolio_id`.
> All API keys, database URLs, and other credentials belong in the backend `.env` file.

Returns: `text/event-stream` (SSE) with events:
- `event: token` → `data: "<JSON-encoded token>"`
- `event: error` → `data: "<user-friendly error message>"`
- `event: final` → `data: "<full formatted response>"`
- `event: done`  → `data: "[DONE]"`

### `POST /api/v1/chat/complete` — Non-streaming fallback

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

---

## 🗄️ Infrastructure: Redis & PostgreSQL

### **Why Redis (Session & Cache Storage)?**

Redis is used for **fast, temporary storage** of user sessions and cached data:

| Benefit | Why We Use It |
|---------|---------------|
| **Speed** | In-memory storage = microsecond response times (vs disk-based databases) |
| **Session TTL** | Auto-expiring keys: portfolio data expires after 1 hour (REDIS_URL: `redis://localhost:6379`) |
| **Real-time** | Ideal for chat sessions, user preferences, conversation history |
| **Simple K-V** | Perfect for session storage (no complex queries needed) |
| **Scalable** | Easy to scale horizontally in production |

**What Redis Stores:**
```
session:{session_id} = {
  "user_id": "user-123",
  "portfolio": {"AAPL": {...}, "INFY": {...}},
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-15T11:30:00Z"  # TTL: 1 hour
}
```

**Why not database?**
- Sessions are temporary (1 hour) → no need for permanent storage
- Sessions accessed on every request → need microsecond speed
- Heavy write load on every request → Redis handles millions of writes/sec

---

### **Why PostgreSQL (Persistent Data)?**

PostgreSQL is used for **permanent storage** of user profiles, portfolios, and historical data. It's essential for financial data because it guarantees ACID compliance (data consistency) and supports complex queries for analytics.

**What PostgreSQL Stores:**
- User profiles and authentication
- Portfolio information
- Holdings (stocks, funds, etc.)
- Transaction history
- Conversation logs

**Why PostgreSQL over SQLite?**
- SQLite works fine for development but locks on writes
- PostgreSQL handles millions of concurrent users with automatic backups and replication
- Critical for financial data that must never be lost or corrupted

---

### **Redis + PostgreSQL Together**

When a user asks a question, the system first checks Redis for their cached portfolio (super fast, 1 microsecond). If found, it uses the cached data. If not found, it queries PostgreSQL and stores the result in Redis for the next request. This way, 99% of requests are lightning fast, and only new sessions hit the slower database.

**Why this architecture?**
- **Speed:** Most requests hit fast Redis (microseconds)
- **Scalability:** PostgreSQL only handles permanent data storage
- **Cost-effective:** Expensive database isn't hit every request
- **Reliable:** If Redis crashes, data is safe in PostgreSQL

---

## 🚀 Hosting & Deployment

### **Local Development (What You Have Now)**

Run Redis, PostgreSQL (optional), backend, and frontend locally. Everything communicates on localhost.

### **Cloud Deployment Options**

#### **Option 1: Docker + AWS**

Package the application in Docker containers and deploy to AWS. Use AWS managed services for Redis (ElastiCache) and PostgreSQL (RDS). Simple and production-ready.

#### **Option 2: Heroku**

Push code to Heroku, which automatically builds and deploys. Add Redis Cloud and Heroku Postgres add-ons. Fastest way to get online.

#### **Option 3: DigitalOcean**

Create a droplet (virtual server), install Docker, and run the application. DigitalOcean also offers managed Redis and PostgreSQL services. Affordable with good control.

#### **Option 4: Kubernetes**

Use Kubernetes for enterprise-scale deployments across multiple servers. Handles auto-scaling, failover, and zero-downtime updates. Complex but powerful for large organizations.

---

### **Deployment Checklist**

| Item | What to Set Up |
|------|----------------|
| **Redis** | In-memory database for session storage |
| **PostgreSQL** | Relational database for permanent data |
| **Backend** | API server (port 8050) |
| **Frontend** | Web interface (port 8501) |
| **SSL/HTTPS** | Secure connections to your domain |
| **Secrets** | API keys stored securely (not in code) |
| **Backups** | Automatic daily database backups |
| **Monitoring** | Use Langfuse to track errors and performance |
| **Scaling** | Auto-scaling when traffic increases |
| **Cost** | Starting at $10-100/month on cloud |

---

### **Production Best Practices**

1. Use strong, randomly generated database passwords
2. Enable SSL/HTTPS on all endpoints
3. Set up automated daily backups
4. Use environment-based secrets (not hardcoded)
5. Enable Redis persistence (saves data to disk)
6. Monitor application with Langfuse and logs
7. Rate limit API to prevent abuse
8. Use CDN for frontend assets
9. Load test before going live
10. Keep dependencies updated for security
