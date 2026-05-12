// UI State and Rendering

const UIState = {
    sessions: {},
    sessionOrder: [],
    currentSessionId: null,
    portfolios: [],
    selectedPortfolioId: null,
    isConnected: false,
};

// Session Management
function createSession() {
    const id = crypto.randomUUID();
    UIState.sessions[id] = {
        id,
        title: "New chat",
        messages: [],
        portfolioId: null,
    };
    UIState.sessionOrder.unshift(id);
    UIState.currentSessionId = id;
    renderUI();
}

function switchSession(id) {
    if (!UIState.sessions[id]) return;
    UIState.currentSessionId = id;
    UIState.sessionOrder.splice(UIState.sessionOrder.indexOf(id), 1);
    UIState.sessionOrder.unshift(id);
    renderUI();
}

function deleteSession(id) {
    delete UIState.sessions[id];
    UIState.sessionOrder = UIState.sessionOrder.filter(sid => sid !== id);
    if (UIState.currentSessionId === id) {
        UIState.currentSessionId = UIState.sessionOrder[0] || null;
    }
    if (!UIState.currentSessionId) {
        createSession();
    }
    renderUI();
}

function getCurrentSession() {
    return UIState.sessions[UIState.currentSessionId] || null;
}

function addMessage(role, content) {
    const session = getCurrentSession();
    if (!session) return;
    session.messages.push({ role, content });
}

function updateSessionTitle(title) {
    const session = getCurrentSession();
    if (session) {
        session.title = title;
    }
}

// Rendering
function renderSessionsList() {
    const list = document.getElementById("sessions-list");
    list.innerHTML = "";

    UIState.sessionOrder.forEach(id => {
        const session = UIState.sessions[id];
        const btn = document.createElement("button");
        btn.className = `session-btn ${id === UIState.currentSessionId ? "active" : ""}`;
        btn.innerHTML = `
            <span>${escapeHtml(session.title)}</span>
            <span class="delete-icon" onclick="event.stopPropagation();">✕</span>
        `;
        btn.onclick = () => switchSession(id);
        btn.querySelector(".delete-icon").onclick = (e) => {
            e.stopPropagation();
            deleteSession(id);
        };
        list.appendChild(btn);
    });
}

async function renderPortfolioList() {
    const select = document.getElementById("portfolio-select");
    select.innerHTML = "";

    if (!UIState.portfolios || UIState.portfolios.length === 0) {
        const emptyOpt = document.createElement("option");
        emptyOpt.value = "";
        emptyOpt.textContent = "No portfolios available";
        emptyOpt.disabled = true;
        select.appendChild(emptyOpt);
        return;
    }

    const defaultOpt = document.createElement("option");
    defaultOpt.value = "";
    defaultOpt.textContent = "Select portfolio...";
    select.appendChild(defaultOpt);

    UIState.portfolios.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.portfolio_id;
        opt.textContent = `${p.name || p.portfolio_id}`;
        select.appendChild(opt);
    });

    const session = getCurrentSession();
    if (session?.portfolioId) {
        select.value = session.portfolioId;
    }
}

async function renderPortfolioStats() {
    const stats = document.getElementById("portfolio-stats");
    const session = getCurrentSession();

    if (!session?.portfolioId) {
        stats.innerHTML = "";
        return;
    }

    const detail = await API.getPortfolioDetail(session.portfolioId);
    stats.innerHTML = "";
    return;
}

function renderMessages() {
    const area = document.getElementById("messages-area");
    const session = getCurrentSession();
    const empty = document.getElementById("empty-state");

    if (!session || session.messages.length === 0) {
        area.style.display = "none";
        empty.style.display = "flex";
        return;
    }

    area.style.display = "flex";
    empty.style.display = "none";
    
    area.innerHTML = session.messages.map(msg => {
        const avatar = msg.role === "user" ? "You" : "AI";
        return `
            <div class="message ${msg.role}">
                <div class="message-avatar">${avatar.charAt(0)}</div>
                <div class="message-wrapper">
                    <div class="message-content">${escapeHtml(msg.content)}</div>
                </div>
            </div>
        `;
    }).join("");

    setTimeout(() => {
        area.scrollTop = area.scrollHeight;
    }, 0);
}

function renderHeader() {
    const session = getCurrentSession();
    const title = document.getElementById("chat-title");
    const subtitle = document.getElementById("header-subtitle");

    if (!session) {
        title.textContent = "Financial Advisor";
        subtitle.textContent = "";
        return;
    }

    title.textContent = session.title;
    if (UIState.streamingStatus) {
        subtitle.textContent = UIState.streamingStatus;
        return;
    }

    const count = session.messages.length;
    subtitle.textContent = count > 0 ? `${count} message${count !== 1 ? 's' : ''}` : "";
}

async function renderStatus() {
    const dot = document.getElementById("status-dot");
    const text = document.getElementById("status-text");

    const isHealthy = await API.checkHealth();
    if (isHealthy) {
        UIState.isConnected = true;
        dot.classList.remove("error");
        text.textContent = "Connected";
    } else {
        UIState.isConnected = false;
        dot.classList.add("error");
        text.textContent = "Disconnected";
    }
}

async function renderUI() {
    renderSessionsList();
    await renderPortfolioList();
    await renderPortfolioStats();
    renderMessages();
    renderHeader();
}

// Utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading() {
    const area = document.getElementById("messages-area");
    area.style.display = "flex";
    const loading = document.createElement("div");
    loading.className = "message assistant";
    loading.innerHTML = '<div class="loading-state"><div class="spinner"></div> Advisor is thinking...</div>';
    loading.id = "loading-message";
    area.appendChild(loading);
    area.scrollTop = area.scrollHeight;
    return loading;
}

function removeLoading() {
    const loading = document.getElementById("loading-message");
    if (loading) loading.remove();
}
