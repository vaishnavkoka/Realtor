#!/bin/bash
# ReAltoR Project Setup Script
# Automates the initial setup process - venv version

set -e

PROJECT_DIR=$(dirname "$(readlink -f "$0")")
cd "$PROJECT_DIR"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   🏠 ReAltoR Real Estate Search Engine - Setup Script      ║"
echo "║       Multi-Agent LangGraph Implementation                 ║"
echo "║       (Python venv version)                                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed or not in PATH"
    exit 1
fi

log_success "Python 3 found"

# Step 1: Create/Setup virtual environment
echo ""
log_info "Step 1: Setting up Python virtual environment..."
if [ -d ".venv" ]; then
    log_warning "Virtual environment '.venv' already exists"
else
    log_info "Creating new Python virtual environment..."
    python3 -m venv .venv
    log_success "Virtual environment created"
fi

# Activate venv
source .venv/bin/activate
log_success "Virtual environment activated"

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
log_success "pip upgraded"

# Install requirements
if [ -f "requirements.txt" ]; then
    log_info "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    log_success "Dependencies installed"
else
    log_error "requirements.txt not found"
    exit 1
fi

# Step 2: Create .env file
echo ""
log_info "Step 2: Configuring environment variables..."
if [ -f ".env" ]; then
    log_warning ".env file already exists"
else
    if [ -f ".env.example" ]; then
        log_info "Creating .env from .env.example..."
        cp .env.example .env
        log_success ".env file created"
        
        log_warning "⚠️  IMPORTANT: You must configure the .env file with your API keys!"
        echo ""
        echo "Required API Keys (Free Tier Available):"
        echo "  1. GROQ_API_KEY → https://console.groq.com/keys"
        echo "  2. HUGGINGFACE_API_KEY → https://huggingface.co/settings/tokens"
        echo "  3. SERPER_API_KEY → https://serper.dev/"
        echo "  4. TAVILY_API_KEY → https://tavily.com/"
        echo "  5. COHERE_API_KEY → https://dashboard.cohere.ai/"
        echo ""
        echo "Edit .env file:"
        echo "  nano .env"
        echo ""
        read -p "Have you configured the .env file with your API keys? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_warning "Please configure .env file before proceeding"
            exit 1
        fi
    else
        log_error ".env.example not found"
        exit 1
    fi
fi

log_success "Environment variables configured"

# Step 3: Display activation instructions
echo ""
log_info "Step 3: Displaying next steps..."
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  SETUP COMPLETE ✓                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "To proceed with the implementation:"
echo ""
echo "1️⃣  Activate the virtual environment:"
echo "    ${BLUE}source .venv/bin/activate${NC}"
echo ""
echo "2️⃣  Initialize the database and vector store:"
echo "    ${BLUE}python src/data_ingestion.py${NC}"
echo ""
echo "3️⃣  Start the backend API server:"
echo "    ${BLUE}python backend.py${NC}"
echo ""
echo "4️⃣  In a new terminal, activate venv and start the frontend:"
echo "    ${BLUE}source .venv/bin/activate${NC}"
echo "    ${BLUE}streamlit run frontend.py${NC}"
echo ""
echo "5️⃣  Access the application:"
echo "    Frontend: ${BLUE}http://localhost:8501${NC}"
echo "    API Docs: ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              📚 DOCUMENTATION                             ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  • IMPLEMENTATION_GUIDE.md - Complete implementation guide║"
echo "║  • README.md - Original project README                    ║"
echo "║  • agents/ - Multi-agent system source code               ║"
echo "║  • ReAltoR.pdf - Technical architecture document          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Setup complete! Configure your API keys and you're ready to go."
echo ""
