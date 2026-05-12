// API Client with Streaming Support

const API = {
    async checkHealth() {
        try {
            const res = await fetch(`${CONFIG.API_BASE_URL}/health`);
            return res.ok;
        } catch {
            return false;
        }
    },

    async getPortfolios() {
        try {
            const res = await fetch(`${CONFIG.API_BASE_URL}/portfolios`);
            if (!res.ok) throw new Error(`Status ${res.status}`);
            return await res.json();
        } catch (error) {
            console.error("Failed to fetch portfolios:", error);
            return [];
        }
    },

    async getPortfolioDetail(portfolioId) {
        try {
            const res = await fetch(`${CONFIG.API_BASE_URL}/portfolios/${portfolioId}`);
            if (!res.ok) throw new Error(`Status ${res.status}`);
            return await res.json();
        } catch (error) {
            console.error("Failed to fetch portfolio detail:", error);
            return null;
        }
    },

    async generateTitle(sessionId, message) {
        try {
            const res = await fetch(`${CONFIG.API_BASE_URL}/chat/title`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sessionId, message }),
            });
            if (!res.ok) throw new Error(`Status ${res.status}`);
            const data = await res.json();
            return data.title || message.slice(0, 40);
        } catch (error) {
            console.error("Failed to generate title:", error);
            return message.slice(0, 40);
        }
    },

    async* streamChat(sessionId, message, portfolioId) {
        const payload = {
            session_id: sessionId,
            message,
            portfolio_id: portfolioId,
        };

        const parseEvent = (rawMessage) => {
            let eventType = "message";
            const dataLines = [];
            const lines = rawMessage.split("\n");

            for (const line of lines) {
                if (line.startsWith(":")) continue;
                if (line.startsWith("event:")) {
                    eventType = line.slice(6).trim();
                } else if (line.startsWith("data:")) {
                    dataLines.push(line.slice(5));
                }
            }

            const rawData = dataLines.join("\n").trim();
            let payload = rawData;
            try {
                payload = JSON.parse(rawData);
            } catch {
                payload = rawData;
            }

            return { type: eventType, payload };
        };

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) throw new Error(`Backend error: ${response.status}`);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    if (buffer.trim()) {
                        buffer = buffer.replace(/\r\n/g, "\n");
                        const messages = buffer.split("\n\n");
                        for (const msg of messages) {
                            if (!msg.trim()) continue;
                            const event = parseEvent(msg);
                            if (event.type === "done" && event.payload === "[DONE]") {
                                yield event;
                                return;
                            }
                            yield event;
                        }
                    }
                    break;
                }

                buffer += decoder.decode(value, { stream: true });
                buffer = buffer.replace(/\r\n/g, "\n");

                const messages = buffer.split("\n\n");
                buffer = messages.pop();

                for (const msg of messages) {
                    if (!msg.trim()) continue;
                    const event = parseEvent(msg);
                    if (event.type === "done" && event.payload === "[DONE]") {
                        yield event;
                        return;
                    }
                    yield event;
                }
            }
        } catch (error) {
            console.error("Stream error:", error);
            yield { type: "error", payload: `Error: ${error.message}` };
        }
    },

    async getNonStreamChat(sessionId, message, portfolioId) {
        const payload = {
            session_id: sessionId,
            message,
            portfolio_id: portfolioId,
        };

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/chat/complete`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error(`Backend error: ${response.status}`);
            }

            const data = await response.json();
            return data.answer || "No response from backend";
        } catch (error) {
            return `Error: ${error.message}`;
        }
    },
};
