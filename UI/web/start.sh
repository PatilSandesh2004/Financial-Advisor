#!/bin/sh

cat > /app/js/config.js <<'EOF'
const CONFIG = {
    API_BASE_URL: "${UI_API_BASE_URL:-http://localhost:8050/api/v1}",
};
window.CONFIG = CONFIG;
EOF

cd /app
python3 << 'PYTHON_EOF'
import http.server
import socketserver
import os

PORT = 8080
STATIC_DIR = "/app"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

os.chdir(STATIC_DIR)
with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
    print(f"Serving at http://0.0.0.0:{PORT}")
    httpd.serve_forever()
PYTHON_EOF
