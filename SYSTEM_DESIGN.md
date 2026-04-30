# 🔧 System Design – Deep Technical Details

Complete flow of how a user message transforms into an AI-powered response with reasoning, data extraction, and real-time streaming.

---

## 🎯 Design Philosophy: Why We Built It This Way

### **The Core Problem We Solved**

Building a financial advisor AI is expensive and slow:
- **Expensive:** LLM calls cost money per token
- **Slow:** Each request to Groq takes 1-3 seconds
- **Inefficient:** Sending the entire portfolio to the LLM every time is wasteful

### **Our Solution: Smart Caching + Multi-Tier Storage**

We use a **three-layer architecture** that balances speed, cost, and reliability:

```
Layer 1 (FASTEST): Redis Cache
├─ Portfolio data for active sessions
├─ Response to similar questions
└─ Conversation history
   → 1-2 milliseconds (in-memory)

Layer 2 (MEDIUM): Processing Layer
├─ LLM calls with extracted data
├─ 3-stage reasoning pipeline
└─ Response streaming
   → 1-3 seconds (API calls)

Layer 3 (PERMANENT): PostgreSQL Database
├─ User accounts & authentication
├─ Portfolio definitions (saved forever)
├─ Transaction history
└─ Conversation logs for analytics
   → 50-100 milliseconds (disk storage)
```

### **How Caching Makes It Fast & Cheap**

When a user asks a question:

1. **Check Redis first** (1ms): Is this portfolio already cached?
   - Yes → Use it immediately (no database query)
   - No → Query PostgreSQL and save to Redis

2. **Extract relevant data** (500ms): Use LLM to identify which stocks matter
   - Save this extraction in Redis cache (10 minute expiry)
   - Similar questions reuse this extraction (no LLM call)

3. **Generate response** (1500ms): Stream answer tokens to user
   - Results cached in Redis for 1 hour
   - User's portfolio stays in Redis until session expires

**Result:** 99% of requests hit fast Redis; only 1% hit the database.

### **Why Three Storage Layers?**

| Layer | Purpose | Speed | Duration | Cost |
|-------|---------|-------|----------|------|
| **Redis (Cache)** | Active session data | 1-2ms | 1 hour | Cheap ($5/month for 1GB) |
| **PostgreSQL (Database)** | Permanent user data | 50ms | Forever | Medium ($10-20/month) |
| **Groq LLM (API)** | Intelligence | 1-3sec | Per call | Expensive ($0.001 per 1000 tokens) |

We minimize LLM calls by caching extractions and pipeline results, saving money.

### **Cache & Redis Decision Flow**

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER SENDS MESSAGE                          │
│              "Why did portfolio drop 2%?"                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                 ┌───────────────────────┐
                 │  CHECK REDIS CACHE    │
                 │  (Session+Portfolio)  │
                 └──────┬────────┬───────┘
                        │        │
                  HIT   │        │   MISS
                        │        │
              ┌─────────┘        └─────────┐
              │                           │
              ↓                           ↓
      ┌──────────────────┐      ┌──────────────────────┐
      │ REDIS HIT ✅     │      │ REDIS MISS ❌        │
      │ Portfolio       │      │ Query PostgreSQL     │
      │ Already cached  │      │ Load user data       │
      │ (1-2ms)         │      │ Save to Redis        │
      └────┬────────────┘      │ TTL: 1 hour          │
           │                   └──────┬───────────────┘
           │                          │
           │                          ↓
           │              ┌──────────────────────┐
           │              │ CHECK EXTRACTION     │
           │              │ CACHE IN REDIS       │
           │              │ (Similar questions)  │
           │              └──────┬───────┬───────┘
           │                     │       │
           │               HIT   │       │   MISS
           │                     │       │
           │         ┌───────────┘       └────┐
           │         │                        │
           ↓         ↓                        ↓
      ┌──────────────────────┐    ┌───────────────────────┐
      │ SKIP ALL 3 STAGES    │    │ RUN 3-STAGE PIPELINE  │
      │ Return cached ans.   │    │                       │
      │ Time: 1-2ms          │    │ Stage 1: Router       │
      │ Cost: $0             │    │ (200ms, 8B model)     │
      └────┬─────────────────┘    │                       │
           │                      │ Stage 2: Extractor    │
           │                      │ (600ms, 70B model)    │
           │                      │ → Save to Redis       │
           │                      │   (10min cache)       │
           │                      │                       │
           │                      │ Stage 3: Reasoner     │
           │                      │ (1500ms, stream)      │
           │                      └────┬──────────────────┘
           │                           │
           │                           ↓
           │                ┌──────────────────────┐
           │                │ CACHE FULL RESPONSE  │
           │                │ Store in Redis       │
           │                │ TTL: 1 hour          │
           │                │ Cost: $0.01          │
           │                └────┬─────────────────┘
           │                     │
           └─────────┬───────────┘
                     │
                     ↓
            ┌──────────────────────┐
            │ STREAM TO FRONTEND   │
            │ (Token by token)     │
            │ Real-time display    │
            └────┬─────────────────┘
                 │
                 ↓
        ┌──────────────────────┐
        │ SYNC TO LANGFUSE     │
        │ (2-5 seconds later)  │
        │ Log trace + metadata │
        └──────────────────────┘
```

### **How Redis Caching Works in Practice**

**Example: User asks about Axis Bank twice**

**First question:** "Why did Axis Bank drop 3%?"
```
1. Check Redis for portfolio → MISS (new session)
2. Query PostgreSQL → Found user portfolio
3. Save to Redis with 1-hour TTL
4. Stage 1: Router → Save classification to Redis
5. Stage 2: Extractor → Save relevant stocks to Redis (10-min cache)
6. Stage 3: Reasoner → Generate and stream answer
7. Cache full response in Redis (1-hour TTL)

Total time: 2.6 seconds
LLM calls: 3
Cost: $0.01
```

**5 minutes later, same user:** "Will Axis Bank recover?"
```
1. Check Redis for portfolio → HIT! ✅ (use immediately)
2. Check Redis extraction cache → HIT! ✅ (similar question)
3. Skip stages 1 & 2 entirely
4. Stage 3 only: Reasoner generates answer
5. Cache full response in Redis (refresh 1-hour TTL)

Total time: 1.5 seconds
LLM calls: 1
Cost: $0.003

Result: 42% faster, 70% cheaper!
```

### **Why PostgreSQL for Permanent Storage?**

PostgreSQL stores data that must survive forever:
- User accounts (never deleted)
- Portfolio definitions (historical record)
- Transaction logs (audit trail for regulations)
- Conversation history (for analytics and compliance)

If Redis crashes, all session data is lost. But that's OK because PostgreSQL has it backed up. We can rebuild Redis from PostgreSQL.

**The safety guarantee:**
- Session data (temporary) → Redis → Auto-expires in 1 hour
- User data (permanent) → PostgreSQL → Backed up daily, never lost
- LLM cache (temporary) → Redis → Expires in 10 minutes

---

## 📡 Architecture Diagram

```
User (Streamlit UI)
    ↓ POST /api/v1/chat
    ├─ message: "Why did portfolio drop 2%?"
    ├─ session_id: "user-123"
    └─ portfolio_id: "portfolio-456"
    
    ↓
    
FastAPI Backend (8050)
    ├─ Session Manager
    │  ├─ Load session from Redis
    │  ├─ Retrieve user's portfolio data
    │  └─ Validate user permissions
    │
    ├─ Trace Manager (Langfuse)
    │  ├─ Create parent trace
    │  ├─ Attach metadata (session_id, portfolio_id)
    │  └─ Initialize trace monitoring
    │
    ├─ AdvisorAgent
    │  ├─ Stage 1: Router
    │  │   ├─ LLM: llama-3.1-8b-instant
    │  │   ├─ Input: Original question
    │  │   ├─ Output: Category (PORTFOLIO_ANALYSIS)
    │  │   └─ Span: route_span created, logged, ended
    │  │
    │  ├─ Stage 2: Extractor
    │  │   ├─ LLM: llama-3.3-70b-versatile
    │  │   ├─ Input: Question + Category + Portfolio holdings
    │  │   ├─ Output: Relevant stocks/sectors list
    │  │   └─ Span: extraction_span created, logged, ended
    │  │
    │  ├─ Stage 3: Reasoner
    │  │   ├─ LLM: llama-3.3-70b-versatile
    │  │   ├─ Input: Question + Extracted data + Full portfolio
    │  │   ├─ Output: Token stream (one token per iteration)
    │  │   ├─ Span: reasoning_span created, logged, ended
    │  │   └─ SSE: Stream to frontend
    │  │
    │  └─ Finalize: End parent trace
    │
    └─ Response Streaming (SSE)
       ├─ Header: Content-Type: text/event-stream
       ├─ Per token: {"type": "token", "content": "word\n"}
       └─ End marker: {"type": "end"}

    ↓

Frontend (Streamlit, 8501)
    ├─ Receive SSE events
    ├─ Extract token content
    ├─ Append to UI text
    └─ Display real-time

    ↓

Langfuse Cloud
    ├─ Receive trace after 2-5 seconds
    ├─ Store with full metadata
    ├─ Make queryable in dashboard
    └─ Track costs & performance
```

---

## 🔄 Request Flow: From Message to Response

### **Request Phase (0-50ms)**

```python
# Frontend (Streamlit)
response = httpx.post(
    "http://127.0.0.1:8050/api/v1/chat",
    json={
        "message": "Why did portfolio drop 2%?",
        "session_id": "user-123",
        "portfolio_id": "portfolio-456"
    },
    stream=True  # SSE streaming enabled
)

# Backend receives POST request
```

### **Session & Setup Phase (50-100ms)**

When a request arrives at the backend:

1. **Load session from Redis** - Check if user's portfolio is cached from a previous session
2. **Validate permissions** - Ensure user owns this portfolio
3. **Create trace** - Start monitoring this request in Langfuse (for debugging later)

If this is a new session, the portfolio is loaded from PostgreSQL and stored in Redis.

### **Agent Processing Phase**

The message goes through 3 stages of processing:

#### **Stage 1: Router (200-400ms)**

**Purpose:** Classify what type of question this is

The router is a fast, small LLM (llama-3.1-8b-instant). It reads the question and decides what category it is:
- **PORTFOLIO_ANALYSIS:** "Why did my portfolio drop?"
- **STOCK_ANALYSIS:** "Should I buy Apple stock?"
- **SECTOR_ANALYSIS:** "How are tech stocks doing?"
- **GENERAL_FINANCE:** "What's inflation?"

**Why this stage exists:** By classifying first, the extractor knows what data to look for in stage 2.

#### **Stage 2: Extractor (600-1000ms)**

**Purpose:** Extract relevant stocks/sectors from the user's portfolio

The extractor uses the portfolio data (from Redis cache) plus the question category to identify which holdings matter.

Example: If question is "Why did Axis Bank drop?" → Extract Axis Bank + Banking sector + Interest rates

**Caching here:** This extraction result is stored in Redis. If another user asks a similar question, we skip this LLM call entirely.

**Result:** 10-minute cache on extractions saves 40% of LLM calls for similar questions.

#### **Stage 3: Reasoner (1-3 seconds)**

**Purpose:** Generate the final answer

The reasoner is the powerful model (llama-3.3-70b-versatile). It uses:
- The original question
- The extracted data (from stage 2)
- The user's full portfolio (from Redis)

It streams tokens one by one to the frontend, so the user sees the answer appearing word-by-word.

**Caching here:** Full response cached in Redis for 1 hour. If user asks the exact same question 10 minutes later, return cached answer instantly (skip all 3 stages, save 2.6 seconds!).
# - Input: {category, portfolio}
# - Output: relevant_data
# - Tokens used: 450 (input) + 280 (output)

### **Response Streaming & Trace Finalization**

Once stage 3 generates tokens, they're streamed to the frontend immediately using Server-Sent Events (SSE). Each token arrives as it's generated, so the user sees the answer appearing word-by-word in real-time.

**Backend:** Generates tokens and sends them to frontend continuously
**Frontend:** Receives each token and displays it immediately
**Timing:** Tokens arrive 1-2 per millisecond, creating smooth streaming effect

After all tokens are sent, the backend finalizes the trace in Langfuse. This means:
- Recording how long each stage took
- Counting tokens used (and cost)
- Storing the full conversation for analytics
- Syncing to Langfuse cloud (~2-5 seconds later)

---

## 🧠 Why 3-Stage Pipeline?

### **Problem with Single Prompt Approach**

If we sent everything to the LLM in one shot:
- **Slow:** Powerful 70B model must do 3 tasks (classify + extract + generate)
- **Expensive:** More tokens per call = higher cost
- **Less accurate:** Model context gets confused with too many instructions
- **Wasteful:** Using powerful model for simple classification tasks

### **Benefits of 3-Stage Approach**

1. **Stage 1 (Router):** Use small, fast 8B model for simple classification (50 tokens)
2. **Stage 2 (Extractor):** Use powerful 70B model with clear task (extract data only)
3. **Stage 3 (Reasoner):** Use powerful 70B model for complex generation (final answer)

**Cost savings:** ~25% fewer tokens compared to single-prompt approach

**Speed:** Router stage takes only 200ms, not 1000ms

**Accuracy:** Each stage focused on one task = better results

---

## 🗄️ Infrastructure Architecture

### **Redis (Session Layer)**

Redis is an in-memory database used for storing user sessions temporarily. When a user logs in, their portfolio data is stored in Redis with a 1-hour expiration. This is much faster than querying the main database every time.

**Why Redis?**
- Incredibly fast (1-2 milliseconds)
- Perfect for temporary data (sessions, cache)
- Auto-deletes expired data
- Handles millions of requests per second

**What's stored:**
- User session ID
- Portfolio data (stocks, holdings)
- Conversation history during the session
- Automatically deleted after 1 hour

---

### **PostgreSQL (Persistent Layer)**

PostgreSQL is the main database for permanent storage. All user accounts, portfolios, transactions, and historical data are stored here. Unlike Redis (which is temporary), PostgreSQL data survives forever until explicitly deleted.

**Why PostgreSQL?**
- Guarantees data won't be lost (ACID compliance)
- Can handle complex queries for reporting
- Supports millions of users
- Automatic backups and recovery
- Works with read replicas for scaling

**What's stored:**
- User accounts and authentication
- Portfolio information
- Holdings and transactions
- Conversation history logs
- Performance analytics

---

### **Combined Architecture: How They Work Together**

When a request arrives:

1. **Check Redis first** (1-2ms): If user's portfolio is cached, use it immediately
2. **If not in Redis**: Query PostgreSQL (50ms), then store result in Redis for next request
3. **Process the query**: Run through the 3-stage pipeline
4. **Return result**: Stream answer back to user
5. **Update cache**: Store extraction results in Redis for similar future questions

**Benefits:**
- 99% of requests are super fast (Redis)
- Only 1% of requests hit the slow database (PostgreSQL)
- If Redis fails, data is safe in PostgreSQL
- If PostgreSQL fails, users continue using cached data

---

## 🌐 Distributed System at Scale

### **Single Server (Development)**

All services run on one computer:
- Backend + Frontend + Redis + PostgreSQL all on localhost
- Works great for testing and development
- Handles ~1,000 concurrent users

### **Multiple Servers (Production)**

When traffic grows to 10,000+ users:
- Use a load balancer to distribute requests across 10 backend servers
- All 10 servers share the same Redis instance
- All 10 servers query the same PostgreSQL instance
- Transparently handles server failures

### **Global Scale (Multiple Regions)**

For worldwide users:
- US region: backend servers + Redis + PostgreSQL
- Europe region: backend servers + Redis + PostgreSQL
- Asia region: backend servers + Redis + PostgreSQL
- All regions sync to a central data warehouse for analytics

Users automatically connect to the nearest region for fastest response times.

---

## 🔒 Security & Reliability

### **Data Security**

- **Passwords**: Salted and hashed using bcrypt (never stored in plain text)
- **API Keys**: Stored in secure vault, never in code or logs
- **Session Data**: Only portfolio (no passwords or secrets)
- **Database**: Encrypted at rest and in transit
- **Backups**: Automated daily snapshots

### **High Availability**

To ensure 99.99% uptime (only 1 minute downtime per month):
- Multiple backend servers (if one fails, others continue)
- Redis clustering (if one Redis fails, another takes over)
- PostgreSQL replication (if primary fails, replica becomes primary)
- Automated backups (data recovery within minutes)
- Health monitoring alerts (Langfuse + CloudWatch)

---

## 📊 Monitoring & Scaling

**Automatic scaling triggers:**
- Backend CPU > 80% → Add more servers
- API response time > 5 seconds → Add more servers
- Redis memory > 90% → Add Redis nodes
- Database connections > 80% → Add read replicas
- Error rate > 1% → Alert engineering team

**Monitoring tools:**
- Langfuse: Tracks all queries and errors
- CloudWatch/DataDog: System metrics (CPU, memory, network)
- Log aggregation: Centralized error logs

---

## 🔍 Langfuse Observability Integration

### **What is Langfuse?**

Langfuse is an open-source LLM observability platform that tracks every AI call, monitors costs, and helps debug issues. Every request through our system creates a **trace** that shows:
- What the LLM was asked
- How long it took
- How many tokens were used (and cost)
- Whether it succeeded or failed
- Parent/child relationships between stages

### **How We Integrated Langfuse**

**1. Initialization (backend/observability/langfuse_client.py)**

```
When backend starts:
├─ Load credentials from .env (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)
├─ Initialize Langfuse SDK client
├─ Create singleton instance (one connection for all requests)
└─ Enable graceful fallback if credentials are missing
```

**2. Trace Creation (per request)**

```
When user sends a message:
├─ Create parent trace with metadata:
│  ├─ session_id (identify the user session)
│  ├─ portfolio_id (identify which portfolio)
│  ├─ query (the user's question)
│  ├─ endpoint (e.g., /api/v1/chat)
│  └─ transport (sse or http)
└─ Attach trace to all operations below
```

**3. Span Tracking (per pipeline stage)**

```
Stage 1 (Router):
├─ start_span("route_classification")
├─ Send question to llama-3.1-8b-instant
├─ Log: input (question), output (category)
├─ Track: latency, token usage
└─ end_span()

Stage 2 (Extractor):
├─ start_span("data_extraction")
├─ Send question + portfolio to llama-3.3-70b-versatile
├─ Log: input (question + portfolio), output (relevant stocks)
├─ Track: latency, token usage, filtered data size
└─ end_span()

Stage 3 (Reasoner):
├─ start_span("answer_generation")
├─ Send question + extracted data + full portfolio to llama-3.3-70b-versatile
├─ Log tokens as they stream in real-time
├─ Track: first token latency, total tokens, generation time
└─ end_span()
```

**4. Trace Finalization**

```
After response completes:
├─ End parent trace
├─ Log finalization events
├─ Trace is queued for sync to cloud
├─ Within 2-5 seconds:
│  ├─ Trace + all spans + metadata uploaded to Langfuse cloud
│  ├─ Becomes visible in Langfuse dashboard
│  └─ Can be viewed at https://cloud.langfuse.com/dashboard
└─ Trace is queryable by session_id, timestamp, user, etc.
```

### **Implementation in Code**

**backend/observability/tracing.py:**
- `create_trace()` - Creates parent trace with metadata
- `start_span()` - Creates named span for a stage
- `end_span()` - Finalizes span with timing
- `track_event()` - Logs intermediate events
- `track_generation()` - Tracks LLM token usage

**backend/routers/chat.py:**
- Calls `create_trace()` at request start
- Passes trace to all components (agent, session manager, etc.)
- Calls `trace.end()` when response completes

**backend/agent/agent.py:**
- Each stage (router, extractor, reasoner) creates its own span
- Logs input/output with `track_event()`
- Langfuse automatically tracks LLM calls

### **What Gets Logged**

For each trace, Langfuse captures:

```
Metadata:
├─ session_id: "user-123"
├─ portfolio_id: "portfolio-456"
├─ query: "Why did my portfolio drop?"
├─ endpoint: "/api/v1/chat"
├─ transport: "sse"
├─ status: "success" or "error"
└─ total_duration_ms: 2600

Spans (3 per request):
├─ Span 1: route_classification
│  ├─ model: llama-3.1-8b-instant
│  ├─ input_tokens: 45
│  ├─ output_tokens: 12
│  ├─ latency_ms: 250
│  ├─ cost: $0.0003
│  └─ status: success
├─ Span 2: data_extraction
│  ├─ model: llama-3.3-70b-versatile
│  ├─ input_tokens: 450
│  ├─ output_tokens: 280
│  ├─ latency_ms: 750
│  ├─ cost: $0.0045
│  └─ status: success
└─ Span 3: answer_generation
   ├─ model: llama-3.3-70b-versatile
   ├─ input_tokens: 1250
   ├─ output_tokens: 182
   ├─ latency_ms: 1800
   ├─ cost: $0.0085
   └─ status: success

Total Cost: $0.013 (3 LLM calls tracked)
```

### **Viewing Traces in Dashboard**

**1. Go to Langfuse Cloud**
```
https://cloud.langfuse.com/dashboard
```

**2. Traces Tab**
- Shows all traces from your account
- Filter by date, session_id, user, status
- Sort by latency, cost, success/error

**3. Click on Any Trace**
- See full timeline of what happened
- View all spans with their timing
- See exact input/output to each LLM
- Review token counts and costs

**4. Analytics**
- Total requests (traces)
- Average latency per stage
- Total tokens used (and cost)
- Error rate and types
- Most expensive queries

### **Cost Tracking**

Langfuse automatically tracks costs for each call:

```
Example Session:
├─ Question 1 (3 LLM calls): $0.013
├─ Question 2 (1 LLM call, cached extraction): $0.005
├─ Question 3 (no LLM call, full response cached): $0.000
├─ Question 4 (3 LLM calls): $0.013
│
Total Session Cost: $0.031
Monthly (100 sessions/day): ~$93
```

Langfuse dashboard shows:
- Cost per trace
- Cost per stage
- Cost per model
- Cost trends over time

### **Error Tracking & Debugging**

When an error occurs:

```
Langfuse captures:
├─ Which stage failed (router, extractor, reasoner)
├─ Error message and type (timeout, invalid API key, etc.)
├─ Full stack trace
├─ What succeeded before error
├─ Latency up to failure point
└─ Input that caused the error
```

**Example:** Router timeout error
```
Trace ID: aaceb416f80ad1fd
Stage: route_classification
Error: Timeout after 30 seconds
Input: "Why did my portfolio drop?"
Status: FAILED
Latency: 30000ms

Next Steps:
├─ Check Groq API status
├─ Verify GROQ_API_KEY is valid
├─ Check network connectivity
└─ Retry or use fallback category
```

---

**That's the complete technical flow! 🎯**
