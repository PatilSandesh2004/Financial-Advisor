#!/bin/sh

cat > /app/js/config.js <<'EOF'
const CONFIG = {
    API_BASE_URL: "${UI_API_BASE_URL:-http://localhost:8050/api/v1}",
};
window.CONFIG = CONFIG;
EOF

cd /app
exec python3 -m http.server --bind 0.0.0.0 8080
