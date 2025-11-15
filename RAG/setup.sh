#!/bin/bash
# RAG System Setup Script
# This script sets up the RAG environment and builds vector indexes

set -e  # Exit on error

echo ""
echo "=========================================="
echo "🚀 RAG System Setup"
echo "=========================================="
echo ""

# Check if we're in the RAG directory
if [[ ! -f "build_vector_index.py" ]]; then
    echo "❌ Error: Must run this script from the RAG/ directory"
    echo "   cd RAG && ./setup.sh"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 not found"
    echo "   Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Check for API key
if [[ -z "${GEMINI_API_KEY}" ]]; then
    echo ""
    echo "⚠️  GEMINI_API_KEY not set"
    echo ""
    read -p "Enter your Gemini API key (or press Enter to skip): " api_key
    
    if [[ -n "$api_key" ]]; then
        export GEMINI_API_KEY="$api_key"
        echo "✓ API key set for this session"
        echo ""
        echo "💡 To make this permanent, add to your ~/.zshrc:"
        echo "   export GEMINI_API_KEY='$api_key'"
    else
        echo "⚠️  Skipping API key setup. You'll need to set it before building indexes."
    fi
else
    echo "✓ GEMINI_API_KEY is set"
fi

echo ""
echo "----------------------------------------"
echo "📦 Installing Dependencies"
echo "----------------------------------------"

# Install requirements
if pip3 install -r requirements.txt --quiet; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "----------------------------------------"
echo "📊 Checking Database Files"
echo "----------------------------------------"

# Check for database files
if [[ ! -f "destination_db.json" ]]; then
    echo "⚠️  destination_db.json not found"
    echo "   You'll need to create or populate this file"
else
    DEST_COUNT=$(python3 -c "import json; print(len(json.load(open('destination_db.json'))))")
    echo "✓ Found destination_db.json with $DEST_COUNT destinations"
fi

if [[ ! -f "experience_db.json" ]]; then
    echo "⚠️  experience_db.json not found"
    echo "   You'll need to create or populate this file"
else
    EXP_COUNT=$(python3 -c "import json; print(len(json.load(open('experience_db.json'))))")
    echo "✓ Found experience_db.json with $EXP_COUNT experiences"
fi

# Check if we should build indexes
if [[ -f "destination_db.json" ]] && [[ -f "experience_db.json" ]] && [[ -n "${GEMINI_API_KEY}" ]]; then
    echo ""
    echo "----------------------------------------"
    echo "🔨 Building Vector Indexes"
    echo "----------------------------------------"
    
    read -p "Build vector indexes now? (y/N): " build_indexes
    
    if [[ "$build_indexes" =~ ^[Yy]$ ]]; then
        echo ""
        python3 build_vector_index.py
        
        if [[ $? -eq 0 ]]; then
            echo ""
            echo "=========================================="
            echo "✅ Setup Complete!"
            echo "=========================================="
            echo ""
            echo "Next steps:"
            echo "  1. Test retrieval: python3 rag_retriever.py"
            echo "  2. Read docs: cat RAG_TECH_STACK.md"
            echo "  3. Build your agents!"
            echo ""
        else
            echo ""
            echo "❌ Index building failed"
            echo "   Check the error messages above"
            exit 1
        fi
    else
        echo ""
        echo "Skipping index building. Run manually when ready:"
        echo "  python3 build_vector_index.py"
    fi
else
    echo ""
    echo "⚠️  Cannot build indexes yet. Missing:"
    [[ ! -f "destination_db.json" ]] && echo "  - destination_db.json"
    [[ ! -f "experience_db.json" ]] && echo "  - experience_db.json"
    [[ -z "${GEMINI_API_KEY}" ]] && echo "  - GEMINI_API_KEY environment variable"
fi

echo ""
echo "=========================================="
echo "Setup script finished"
echo "=========================================="
echo ""
