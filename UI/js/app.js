// Main App Logic

window.addEventListener("DOMContentLoaded", async () => {
    // Initialize
    createSession();
    UIState.portfolios = await API.getPortfolios();
    await renderUI();
    await renderStatus();

    // Periodic status check
    setInterval(renderStatus, 5000);

    // Event: New Chat
    document.getElementById("new-chat").addEventListener("click", () => {
        createSession();
    });

    // Event: Portfolio Selection
    document.getElementById("portfolio-select").addEventListener("change", async (e) => {
        const session = getCurrentSession();
        if (session) {
            session.portfolioId = e.target.value || null;
            await renderPortfolioStats();
        }
    });

    // Event: Message Input Auto-resize
    const input = document.getElementById("message-input");
    input.addEventListener("input", (e) => {
        e.target.style.height = "auto";
        e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
    });

    // Event: Form Submit
    document.getElementById("message-form").addEventListener("submit", async (e) => {
        e.preventDefault();

        const message = input.value.trim();
        if (!message) return;

        const session = getCurrentSession();
        if (!session) return;

        // Add user message
        addMessage("user", message);
        input.value = "";
        input.style.height = "auto";
        renderMessages();

        // Generate title if new
        if (session.title === "New chat") {
            session.title = await API.generateTitle(session.id, message);
            renderHeader();
            renderSessionsList();
        }

        // Show loading state while the answer streams
        UIState.isStreaming = true;
        UIState.streamingStatus = "Advisor is thinking...";
        renderHeader();

        let assistantIndex = null;
        let fullResponse = "";

        try {
            for await (const chunk of API.streamChat(session.id, message, session.portfolioId)) {
                if (!chunk) continue;

                if (chunk.type === "thinking") {
                    const payload = chunk.payload;
                    const status = payload?.message || payload?.step || payload?.type || "Thinking...";
                    UIState.streamingStatus = `Thinking: ${status}`;
                    renderHeader();
                    continue;
                }

                if (chunk.type === "done") {
                    break;
                }

                if (chunk.type === "error") {
                    fullResponse = `Error: ${chunk.payload}`;
                    addMessage("assistant", fullResponse);
                    renderMessages();
                    break;
                }

                if (chunk.type === "token" || chunk.type === "final" || chunk.type === "message") {
                    const text = typeof chunk.payload === "string" ? chunk.payload : String(chunk.payload);
                    fullResponse += text;

                    if (assistantIndex === null) {
                        addMessage("assistant", fullResponse);
                        assistantIndex = getCurrentSession().messages.length - 1;
                    } else {
                        const messages = getCurrentSession().messages;
                        if (messages[assistantIndex]) {
                            messages[assistantIndex].content = fullResponse;
                        }
                    }

                    renderMessages();
                }
            }
        } catch (error) {
            fullResponse = `Error: ${error.message}`;
            addMessage("assistant", fullResponse);
            renderMessages();
        } finally {
            UIState.isStreaming = false;
            UIState.streamingStatus = "";
            renderHeader();
        }
    });
});

// Expose functions for inline handlers
window.deleteSession = deleteSession;
