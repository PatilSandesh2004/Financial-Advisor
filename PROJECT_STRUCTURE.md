# 📁 Project Structure – File Organization & Purpose

Complete directory tree with explanations of what each file does and how components interact.

---

## 🌳 Directory Tree

```
Financial-Advisor/
│
├── 📄 README.md                          ← Start here! Setup & overview
├── 📄 SYSTEM_DESIGN.md                   ← Technical deep-dive (query flow)
├── 📄 PROJECT_STRUCTURE.md               ← This file (file organization)
├── 📄 requirements.txt                   ← Python dependencies
├── 📄 .env                               ← Configuration & API keys
├── 📄 .env.example                       ← Template for .env
│
├── 📁 backend/                           ← FastAPI server (port 8050)
│   ├── 📄 main.py                        ← App initialization, routes setup
│   │   ├─ Creates FastAPI instance
│   │   ├─ Registers routers
│   │   ├─ Sets up CORS for frontend
│   │   └─ Starts on http://127.0.0.1:8050
│   │
│   ├── 📁 routers/
│   │   ├── 📄 chat.py                    ← POST /api/v1/chat endpoint
│   │   │   ├─ Receives user message + session_id + portfolio_id
│   │   │   ├─ Loads session from Redis
│   │   │   ├─ Creates Langfuse trace
│   │   │   ├─ Calls AdvisorAgent
│   │   │   └─ Streams response via SSE
│   │   │
│   │   └── 📄 health.py                  ← GET /api/v1/health endpoint
│   │       ├─ Returns {"status": "ok"}
│   │       └─ Used for monitoring backend availability
│   │
│   ├── 📁 agent/
│   │   └── 📄 agent.py                   ← 3-stage reasoning pipeline
│   │       ├─ Stage 1: Router (classify question)
│   │       │  ├─ Model: llama-3.1-8b-instant (fast)
│   │       │  ├─ Input: user message
│   │       │  └─ Output: category (PORTFOLIO_ANALYSIS, etc)
│   │       │
│   │       ├─ Stage 2: Extractor (find relevant data)
│   │       │  ├─ Model: llama-3.3-70b-versatile (powerful)
│   │       │  ├─ Input: question + category + portfolio
│   │       │  └─ Output: list of relevant stocks/sectors
│   │       │
│   │       ├─ Stage 3: Reasoner (generate answer)
│   │       │  ├─ Model: llama-3.3-70b-versatile (powerful)
│   │       │  ├─ Input: all extracted data
│   │       │  ├─ Output: token stream (streaming)
│   │       │  └─ Each token traced to Langfuse
│   │       │
│   │       └─ Logging: 50+ print statements for debugging
│   │
│   ├── 📁 observability/
│   │   ├── 📄 langfuse_client.py         ← Singleton Langfuse client
│   │   │   ├─ Initializes on first use
│   │   │   ├─ Loads credentials from .env
│   │   │   ├─ Gracefully disables if credentials missing
│   │   │   └─ Used by tracing.py
│   │   │
│   │   └── 📄 tracing.py                 ← Trace/span wrapper API
│   │       ├─ create_trace()             ← Start parent trace
│   │       ├─ start_span()               ← Start child span
│   │       ├─ track_event()              ← Log an event in trace
│   │       ├─ track_generation()         ← Track LLM generation
│   │       └─ Direct SDK calls (no generic fallback)
│   │
│   ├── 📁 session/
│   │   └── 📄 redis_manager.py           ← Session storage layer
│   │       ├─ get_session()              ← Load session from Redis
│   │       ├─ set_session()              ← Save session to Redis
│   │       ├─ delete_session()           ← Clear session
│   │       ├─ URL: redis://localhost:6379
│   │       └─ TTL: 3600 seconds (1 hour)
│   │
│   └── 📁 config/
│       └── 📄 settings.py                ← Environment configuration
│           ├─ Loads from .env
│           ├─ Provides validated settings
│           └─ Used by all backend modules
│
├── 📁 frontend/                          ← Streamlit UI (port 8501)
│   ├── 📄 app.py                         ← Main Streamlit app
│   │   ├─ Chat interface
│   │   ├─ Session management
│   │   ├─ SSE streaming from backend
│   │   ├─ Token-by-token display
│   │   └─ Runs on http://localhost:8501
│   │
│   └── 📄 styles.py                      ← CSS & styling
│       ├─ Custom Streamlit themes
│       ├─ UI component styling
│       └─ Visual configuration
│
├── 📁 tests/                             ← Unit & integration tests
│   ├── 📄 test_chat.py                   ← Test /api/v1/chat endpoint
│   ├── 📄 test_agent.py                  ← Test 3-stage pipeline
│   └── 📄 test_session.py                ← Test Redis session management
│
└── 📁 scripts/                           ← Utility scripts
    ├── 📄 monitor_langfuse.sh            ← Watch traces in dashboard
    └── 📄 test_backend.py                ← Manual backend testing
```

---

## 🔗 Component Interaction Map

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Streamlit)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ app.py - Chat Interface                                │   │
│  │ ├─ Display chat history                               │   │
│  │ ├─ Accept user input                                 │   │
│  │ ├─ Call backend POST /api/v1/chat                   │   │
│  │ └─ Render SSE tokens in real-time                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓↑ HTTP                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI, 8050)                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ main.py - App Setup                                    │   │
│  │ ├─ FastAPI instance                                   │   │
│  │ ├─ CORS configuration                                 │   │
│  │ └─ Router registration                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│             ↓                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ routers/chat.py - POST /api/v1/chat                   │   │
│  │ ├─ Receives message, session_id, portfolio_id         │   │
│  │ ├─ Calls redis_manager.get_session()      ──────┐    │   │
│  │ ├─ Calls tracer.create_trace()    ────────┐     │    │   │
│  │ ├─ Calls agent.process()          ────────┼────┬┴──┐ │   │
│  │ └─ Streams response via SSE                │    │   │ │   │
│  └──────────────────────────────────────────────────────────┘   │
│             ↓                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ agent/agent.py - 3-Stage Pipeline                      │   │
│  │                                                          │   │
│  │ Stage 1: Router                                         │   │
│  │ ├─ Input: message                                       │   │
│  │ ├─ Model: llama-3.1-8b-instant (Groq)                 │   │
│  │ └─ Output: category                                     │   │
│  │                                                          │   │
│  │ Stage 2: Extractor                                      │   │
│  │ ├─ Input: message + category + portfolio [from Redis]  │   │
│  │ ├─ Model: llama-3.3-70b-versatile (Groq)             │   │
│  │ └─ Output: relevant stocks/sectors                      │   │
│  │                                                          │   │
│  │ Stage 3: Reasoner (Streaming)                           │   │
│  │ ├─ Input: all extracted data                            │   │
│  │ ├─ Model: llama-3.3-70b-versatile (Groq)             │   │
│  │ ├─ Output: token stream                                 │   │
│  │ └─ Logs to Langfuse:                                    │   │
│  │    tracer.start_span() → for each token → end()        │   │
│  └──────────────────────────────────────────────────────────┘   │
│    ↓ (session data)     ↓ (traces)           ↓ (LLM calls)     │
└────┬────────────────────┬───────────────────┬────────────────────┘
     │                    │                   │
     ↓                    ↓                   ↓
┌─────────────┐  ┌──────────────────┐  ┌─────────────────┐
│   Redis     │  │     Langfuse     │  │   Groq API      │
│   6379      │  │   Cloud Platform │  │   chat.groq.com │
│             │  │                  │  │                 │
│ Session     │  │ Traces & Spans   │  │ - llama-3.1-8b  │
│ Storage     │  │ Metadata         │  │ - llama-3.3-70b │
│ TTL: 1hr    │  │ Debugging        │  │                 │
│             │  │ Performance      │  │ Returns tokens  │
└─────────────┘  └──────────────────┘  └─────────────────┘
```

---

## 📊 Data Flow Through Files

### **User Query → Response Flow**

```
1. Frontend: app.py
   └─ User types: "Why did portfolio drop 2%?"
   └─ Click Send → POST /api/v1/chat

2. Backend: routers/chat.py
   └─ Receive POST request
   └─ Extract: message, session_id, portfolio_id
   └─ Call: redis_manager.get_session(session_id)

3. Session Manager: session/redis_manager.py
   └─ Query Redis: key = f"session:{session_id}"
   └─ Return: {"user_id": "...", "portfolio": {...}, "created_at": "..."}
   └─ Portfolio data: {"AAPL": {...}, "INFY": {...}, ...}

4. Trace Manager: routers/chat.py + observability/tracing.py
   └─ Call: create_trace("financial-advisor-chat", ...)
   └─ Uses: langfuse_client.py (singleton)
   └─ Langfuse cloud starts tracking this trace

5. Agent: agent/agent.py
   ├─ Stage 1: Router
   │  └─ Input: "Why did portfolio drop 2%?"
   │  └─ Call: Groq llama-3.1-8b-instant
   │  └─ Output: "PORTFOLIO_ANALYSIS"
   │  └─ Log to: tracer.start_span() → tracer.end()
   │
   ├─ Stage 2: Extractor
   │  └─ Input: question + category + portfolio (from Redis)
   │  └─ Call: Groq llama-3.3-70b-versatile
   │  └─ Output: "AXIS, Banking sector, RBI rate policy"
   │  └─ Log to: tracer.start_span() → tracer.end()
   │
   └─ Stage 3: Reasoner
      └─ Input: question + category + extracted_data + portfolio
      └─ Call: Groq llama-3.3-70b-versatile (streaming)
      └─ For each token:
         ├─ tracer.track_generation() for token
         ├─ Yield token to frontend via SSE
      └─ Log to: tracer.start_span() → tracer.end()

6. Frontend: app.py
   └─ Receive SSE event stream
   └─ For each event:
      ├─ Parse: {"type": "token", "content": "word"}
      ├─ Append to response_text
      ├─ Display in styles.py styled UI

7. Langfuse Cloud
   └─ Wait 2-5 seconds
   └─ Receive full trace from backend
   └─ Show in dashboard:
      ├─ Parent trace metadata
      ├─ Child spans with durations
      ├─ Token counts
      └─ Latencies for each stage
```

---

## 🔑 Key Files Explained

### **backend/main.py** – App Initialization

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import chat, health

app = FastAPI()

# CORS: Allow frontend to make requests
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

# Include routers
app.include_router(chat.router)
app.include_router(health.router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8050)
```

**Purpose:** Entry point for backend server. Sets up FastAPI, routes, middleware.

---

### **backend/routers/chat.py** – Chat Endpoint

```python
@router.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):
    # 1. Load session from Redis
    session = redis_manager.get_session(request.session_id)
    
    # 2. Create trace
    trace = create_trace("financial-advisor-chat", 
                        session_id=request.session_id, ...)
    
    # 3. Process with agent
    async for token in agent.process(request.message, session):
        yield f'data: {json.dumps({"type": "token", "content": token})}\n\n'
    
    # 4. End trace
    trace.end()
```

**Purpose:** HTTP endpoint that orchestrates the entire request. Connects session manager, trace manager, and agent.

---

### **backend/agent/agent.py** – 3-Stage Pipeline

```python
class AdvisorAgent:
    def process(self, message, session):
        # Stage 1: Classify question
        category = self.route(message)
        
        # Stage 2: Extract relevant data
        relevant_data = self.extract(message, category, session.portfolio)
        
        # Stage 3: Generate answer (streaming)
        for token in self.reason(message, category, relevant_data, session.portfolio):
            yield token
```

**Purpose:** Implements the 3-stage reasoning pipeline. Each stage uses different LLM models.

---

### **backend/observability/langfuse_client.py** – Tracing Client

```python
class LangfuseClient:
    _instance = None  # Singleton
    
    def __init__(self):
        # Load credentials from .env
        self.client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            base_url=os.getenv("LANGFUSE_BASE_URL")
        )
```

**Purpose:** Singleton client for Langfuse. Safely initializes once, used by tracing.py.

---

### **backend/observability/tracing.py** – Trace API

```python
def create_trace(name, session_id, portfolio_id, ...):
    """Create parent trace"""
    return Trace(langfuse_client.client.start_observation(
        name=name, 
        as_type="span",
        metadata={"session_id": session_id, ...}
    ))

class Trace:
    def start_span(self, name):
        """Create child span"""
        return Span(self._trace.start_observation(name=name, as_type="span"))
```

**Purpose:** Wrapper API for Langfuse. Simplifies trace/span creation with error handling.

---

### **backend/session/redis_manager.py** – Session Storage

```python
def get_session(session_id):
    """Load session from Redis"""
    key = f"session:{session_id}"
    data = redis_client.get(key)
    return json.loads(data) if data else None

def set_session(session_id, data):
    """Save session to Redis with 1-hour TTL"""
    key = f"session:{session_id}"
    redis_client.setex(key, 3600, json.dumps(data))
```

**Purpose:** Abstraction layer for Redis. Manages session storage and TTL.

---

### **frontend/app.py** – Streamlit UI

```python
st.title("Financial Advisor")

message = st.chat_input("Ask about your portfolio...")

if message:
    # Send to backend
    response = httpx.post(
        "http://127.0.0.1:8050/api/v1/chat",
        json={"message": message, "session_id": ..., "portfolio_id": ...},
        stream=True
    )
    
    # Render SSE stream
    response_text = ""
    for line in response.iter_lines():
        if line.startswith("data: "):
            event = json.loads(line[6:])
            if event["type"] == "token":
                response_text += event["content"]
                st.markdown(response_text)
```

**Purpose:** Main UI. Displays chat interface, sends requests, renders real-time tokens.

---

### **.env** – Configuration

```env
# LLM API Keys
GROQ_API_KEY=your_key
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_ROUTER_MODEL=llama-3.1-8b-instant

# Tracing
LANGFUSE_PUBLIC_KEY=your_key
LANGFUSE_SECRET_KEY=your_secret
LANGFUSE_BASE_URL=https://cloud.langfuse.com

# Session Storage
REDIS_URL=redis://localhost:6379

# System
API_BASE_URL=http://127.0.0.1:8050
LOG_LEVEL=INFO
```

**Purpose:** Environment variables. Loaded by config/settings.py.

---

### **requirements.txt** – Dependencies

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
streamlit==1.28.0
langfuse==2.0.0
groq==0.4.0
redis==5.0.0
httpx==0.25.0
python-dotenv==1.0.0
pydantic==2.4.0
```

**Purpose:** Python package list. Install with: `pip install -r requirements.txt`

---

## 🔄 Execution Flow Diagram

```
Step 1: User Asks Question
    ↓
Frontend (Streamlit)
    └─ app.py receives input
    └─ Calls: httpx.post("/api/v1/chat")
    
    ↓
Step 2: Backend Receives Request
    ↓
Backend Router
    └─ routers/chat.py
    └─ Extracts: message, session_id, portfolio_id
    
    ↓
Step 3: Load Session
    ↓
Redis Manager
    └─ session/redis_manager.py
    └─ Fetches user portfolio from Redis
    └─ Returns: portfolio dict
    
    ↓
Step 4: Start Tracing
    ↓
Tracing & Langfuse
    └─ observability/tracing.py
    └─ Creates parent trace with metadata
    └─ Langfuse cloud notified (trace RUNNING)
    
    ↓
Step 5: Process with Agent
    ↓
Agent Pipeline
    └─ agent/agent.py
    
    Stage 1: Router
    ├─ Input: message
    ├─ Model: llama-3.1-8b-instant (Groq)
    ├─ Output: category
    └─ Log: tracer.start_span() → tracer.end()
    
    Stage 2: Extractor
    ├─ Input: message + category + portfolio
    ├─ Model: llama-3.3-70b-versatile (Groq)
    ├─ Output: relevant_data
    └─ Log: tracer.start_span() → tracer.end()
    
    Stage 3: Reasoner (Streaming)
    ├─ Input: all extracted data
    ├─ Model: llama-3.3-70b-versatile (Groq)
    ├─ For each token:
    │  ├─ Get token from LLM
    │  ├─ Log: tracer.track_generation()
    │  ├─ Yield to frontend
    └─ End: tracer.end()
    
    ↓
Step 6: Stream Tokens to Frontend
    ↓
SSE Response
    └─ routers/chat.py yields
    └─ data: {"type": "token", "content": "word"}
    └─ Frontend receives in real-time
    
    ↓
Step 7: Finalize Trace
    ↓
Langfuse
    └─ tracer.end() called
    └─ Trace queued for sync
    └─ 2-5 seconds later appears in dashboard
    
    ↓
Step 8: Frontend Renders
    ↓
Streamlit
    └─ app.py updates UI
    └─ Tokens append to response_text
    └─ User sees answer appearing word-by-word
```

---

## 🎯 File Dependencies

```
app.py (Frontend)
    ↓ HTTP POST
    └─→ main.py (Backend initialization)
        └─→ routers/chat.py
            ├─→ session/redis_manager.py (load portfolio)
            ├─→ observability/tracing.py (create trace)
            │   └─→ observability/langfuse_client.py (Langfuse SDK)
            ├─→ agent/agent.py (3-stage pipeline)
            │   ├─→ Groq API (llm calls)
            │   └─→ observability/tracing.py (log spans)
            └─→ config/settings.py (load .env)
```

---

## 🚀 Starting the System

### **1. Backend**

```bash
cd /home/sandeshpatil/Downloads/Financial-Advisor/Financial-Advisor
export PYTHONPATH=$PWD
python3 -m uvicorn backend.main:app --port 8050 --reload
```

**What runs:**
- main.py initializes FastAPI
- Registers routers from routers/chat.py and routers/health.py
- Backend listens on http://127.0.0.1:8050

### **2. Frontend**

```bash
cd /home/sandeshpatil/Downloads/Financial-Advisor/Financial-Advisor
set -a && source .env && set +a
streamlit run frontend/app.py --server.port 8501
```

**What runs:**
- app.py loads Streamlit
- Loads environment from .env
- Frontend listens on http://localhost:8501

### **3. Redis (Session Storage)**

```bash
docker run -d -p 6379:6379 redis:alpine
```

**What runs:**
- Redis server on localhost:6379
- Stores user sessions (1-hour TTL)

---

## 📞 File Interconnections

| Caller | Called File | Purpose |
|--------|------------|---------|
| app.py | chat.py | Send message to backend |
| chat.py | redis_manager.py | Load portfolio session |
| chat.py | tracing.py | Create parent trace |
| chat.py | agent.py | Process query |
| agent.py | Groq API | Call LLM |
| agent.py | tracing.py | Log spans |
| tracing.py | langfuse_client.py | Get Langfuse client |
| agent.py | main.py | Configured via settings.py |
| app.py | main.py | Backend URL from .env |

---

**Now you understand the entire architecture! 🎉**
