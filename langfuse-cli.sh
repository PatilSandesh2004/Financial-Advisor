#!/bin/bash

##############################################################################
# Langfuse Tracing - Financial Advisor Setup & Monitoring Script
# Run this script to quickly validate and monitor your Langfuse integration
##############################################################################

PROJECT_DIR="/home/sandeshpatil/Downloads/Financial-Advisor/Financial-Advisor"
VENV_PATH="/home/sandeshpatil/Downloads/Financial-Advisor/.venv"
PYTHON="${VENV_PATH}/bin/python"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

##############################################################################
# Functions
##############################################################################

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

##############################################################################
# Main Script
##############################################################################

case "$1" in
    "validate")
        print_header "🔍 VALIDATING LANGFUSE INTEGRATION"
        
        print_info "Running validation script..."
        cd "$PROJECT_DIR"
        $PYTHON test_langfuse_validation.py
        
        if [ $? -eq 0 ]; then
            print_success "Validation completed successfully!"
        else
            print_error "Validation failed. Check output above."
            exit 1
        fi
        ;;
        
    "backend")
        print_header "🖥️  STARTING BACKEND SERVER"
        
        print_info "Starting FastAPI backend on port 8050..."
        cd "$PROJECT_DIR"
        $PYTHON -m uvicorn backend.main:app --reload --port 8050
        ;;
        
    "frontend")
        print_header "📱 STARTING STATIC UI"
        
        print_info "Loading environment variables..."
        cd "$PROJECT_DIR/UI"
        set -a
        source ../.env
        set +a
        
        print_info "Starting UI on port 8080..."
        $PYTHON -m http.server 8080
        ;;
        
    "monitor")
        print_header "📊 LANGFUSE DASHBOARD"
        
        print_info "Opening Langfuse dashboard..."
        echo ""
        echo "Dashboard URL: https://cloud.langfuse.com"
        echo ""
        print_info "Instructions:"
        echo "  1. Login with your credentials"
        echo "  2. Click: Tracing → Traces"
        echo "  3. Look for: 'financial-advisor-chat'"
        echo "  4. Click to expand trace hierarchy"
        echo ""
        
        # Try to open in browser (if available)
        if command -v xdg-open &> /dev/null; then
            xdg-open "https://cloud.langfuse.com"
        elif command -v open &> /dev/null; then
            open "https://cloud.langfuse.com"
        else
            print_info "Manually open: https://cloud.langfuse.com"
        fi
        ;;
        
    "frontend-ui")
        print_header "🌐 OPENING UI"
        
        print_info "Opening UI..."
        echo ""
        echo "UI URL: http://localhost:8080"
        echo ""
        print_info "Instructions:"
        echo "  1. Type a message (e.g., 'What are the risks?')"
        echo "  2. Press Enter"
        echo "  3. Wait for response (3-5 seconds)"
        echo "  4. Check backend terminal for logs"
        echo ""
        
        # Try to open in browser (if available)
        if command -v xdg-open &> /dev/null; then
            xdg-open "http://localhost:8080"
        elif command -v open &> /dev/null; then
            open "http://localhost:8080"
        else
            print_info "Manually open: http://localhost:8080"
        fi
        ;;
        
    "docs")
        print_header "📚 DOCUMENTATION"
        
        echo "Available documentation files:"
        echo ""
        echo -e "${CYAN}1. README_LANGFUSE.md${NC}"
        echo "   → Main quick start guide (START HERE)"
        echo "   → Read in: less README_LANGFUSE.md"
        echo ""
        echo -e "${CYAN}2. LANGFUSE_VALIDATION_REPORT.md${NC}"
        echo "   → Comprehensive validation & troubleshooting"
        echo "   → Read in: less LANGFUSE_VALIDATION_REPORT.md"
        echo ""
        echo -e "${CYAN}3. MONITOR_LANGFUSE.sh${NC}"
        echo "   → Quick reference guide"
        echo "   → View in: less MONITOR_LANGFUSE.sh"
        echo ""
        echo -e "${CYAN}4. TRACE_EXAMPLE.json${NC}"
        echo "   → Real trace example"
        echo "   → View in: cat TRACE_EXAMPLE.json"
        echo ""
        echo -e "${CYAN}5. COMPLETION_SUMMARY.md${NC}"
        echo "   → Project completion summary"
        echo "   → View in: less COMPLETION_SUMMARY.md"
        echo ""
        ;;
        
    "check")
        print_header "🔧 SYSTEM CHECKS"
        
        echo "Checking prerequisites..."
        echo ""
        
        # Check Python
        if command -v $PYTHON &> /dev/null; then
            VERSION=$($PYTHON --version 2>&1)
            print_success "Python: $VERSION"
        else
            print_error "Python not found"
            exit 1
        fi
        
        # Check Redis
        if redis-cli ping &> /dev/null; then
            print_success "Redis: Running"
        else
            print_warning "Redis: Not running (needed for session storage)"
        fi
        
        # Check ports
        echo ""
        print_info "Checking ports..."
        
        if ! lsof -i :8050 &> /dev/null; then
            print_success "Port 8050: Available"
        else
            print_warning "Port 8050: In use"
        fi
        
        if ! lsof -i :8501 &> /dev/null; then
            print_success "Port 8501: Available"
        else
            print_warning "Port 8501: In use"
        fi
        
        # Check env variables
        echo ""
        print_info "Checking environment variables..."
        
        cd "$PROJECT_DIR"
        if grep -q "LANGFUSE_PUBLIC_KEY" .env; then
            print_success "LANGFUSE_PUBLIC_KEY: Set"
        else
            print_error "LANGFUSE_PUBLIC_KEY: Not set"
        fi
        
        if grep -q "LANGFUSE_SECRET_KEY" .env; then
            print_success "LANGFUSE_SECRET_KEY: Set"
        else
            print_error "LANGFUSE_SECRET_KEY: Not set"
        fi
        
        if grep -q "API_BASE_URL" .env; then
            print_success "API_BASE_URL: Set"
        else
            print_error "API_BASE_URL: Not set"
        fi
        
        echo ""
        print_success "All checks completed!"
        ;;
        
    "quick-start")
        print_header "🚀 QUICK START GUIDE"
        
        echo "Follow these steps to get started:"
        echo ""
        
        echo -e "${CYAN}Step 1: Validate Setup${NC} (1 minute)"
        echo "  Run: $0 validate"
        echo "  Expected output: 🟢 LANGFUSE TRACING READY"
        echo ""
        
        echo -e "${CYAN}Step 2: Start Backend${NC} (Terminal 1)"
        echo "  Run: $0 backend"
        echo "  Expected output: Application startup complete"
        echo ""
        
        echo -e "${CYAN}Step 3: Start Frontend${NC} (Terminal 2)"
        echo "  Run: $0 frontend"
        echo "  Expected output: You can now view your Streamlit app"
        echo ""
        
        echo -e "${CYAN}Step 4: Open UI${NC} (1 minute)"
        echo "  Run: $0 frontend-ui"
        echo "  Or open: http://localhost:8501"
        echo ""
        
        echo -e "${CYAN}Step 5: Send Message${NC}"
        echo "  Type: 'What are the risks of my portfolio?'"
        echo "  Wait: 3-5 seconds for response"
        echo "  Watch: Backend terminal for logs"
        echo ""
        
        echo -e "${CYAN}Step 6: View Trace${NC} (1 minute)"
        echo "  Run: $0 monitor"
        echo "  Or open: https://cloud.langfuse.com"
        echo "  Look for: Latest trace named 'financial-advisor-chat'"
        echo ""
        
        echo -e "${GREEN}Done! Your tracing system is now active!${NC}"
        echo ""
        ;;
        
    "help"|"")
        print_header "📖 LANGFUSE TRACING - QUICK COMMANDS"
        
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo ""
        echo -e "${CYAN}  validate${NC}"
        echo "    Validate Langfuse integration setup"
        echo "    Run this first to verify everything is working"
        echo ""
        echo -e "${CYAN}  backend${NC}"
        echo "    Start FastAPI backend server (port 8050)"
        echo "    Run in Terminal 1"
        echo ""
        echo -e "${CYAN}  frontend${NC}"
        echo "    Start Streamlit UI (port 8501)"
        echo "    Run in Terminal 2"
        echo ""
        echo -e "${CYAN}  monitor${NC}"
        echo "    Open Langfuse dashboard"
        echo "    View traces at: https://cloud.langfuse.com"
        echo ""
        echo -e "${CYAN}  frontend-ui${NC}"
        echo "    Open Streamlit UI"
        echo "    Browse to: http://localhost:8501"
        echo ""
        echo -e "${CYAN}  check${NC}"
        echo "    Check system prerequisites"
        echo "    Verifies Python, Redis, ports, environment"
        echo ""
        echo -e "${CYAN}  docs${NC}"
        echo "    Show available documentation files"
        echo ""
        echo -e "${CYAN}  quick-start${NC}"
        echo "    Show complete quick start guide"
        echo ""
        echo -e "${CYAN}  help${NC}"
        echo "    Show this help message"
        echo ""
        
        echo "Examples:"
        echo "  $0 validate           # Check if Langfuse is ready"
        echo "  $0 backend            # Start backend server"
        echo "  $0 frontend           # Start Streamlit UI"
        echo "  $0 monitor            # View Langfuse dashboard"
        echo "  $0 check              # Check prerequisites"
        echo ""
        
        echo -e "${YELLOW}Recommended workflow:${NC}"
        echo "  1. $0 quick-start       # Read the guide"
        echo "  2. $0 validate          # Verify setup"
        echo "  3. $0 check             # Check system"
        echo "  4. $0 backend           # Start backend (Terminal 1)"
        echo "  5. $0 frontend          # Start frontend (Terminal 2)"
        echo "  6. $0 frontend-ui       # Open UI"
        echo "  7. Send message from UI"
        echo "  8. $0 monitor           # View trace"
        echo ""
        ;;
        
    *)
        print_error "Unknown command: $1"
        echo ""
        echo "Run '$0 help' for available commands"
        exit 1
        ;;
esac

exit 0
