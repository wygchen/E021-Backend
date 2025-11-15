#!/bin/bash

# Simple test script to verify the RAG integration works
# This script sets up the environment and runs the test

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "======================================================================"
echo "🧪 Testing RAG Integration"
echo "======================================================================"
echo ""

# Check for GEMINI_API_KEY
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Warning: GEMINI_API_KEY not set${NC}"
    echo "The agent will still import, but RAG searches will fail."
    echo ""
    echo "To set your API key, run:"
    echo "  export GEMINI_API_KEY='your-api-key-here'"
    echo ""
fi

# Check for vector indexes
if [ ! -f "RAG/vector_indexes/destination_index.pkl" ]; then
    echo -e "${RED}❌ Error: destination_index.pkl not found${NC}"
    echo "Please build the vector indexes first:"
    echo "  cd RAG"
    echo "  python build_vector_index.py"
    echo ""
    exit 1
fi

if [ ! -f "RAG/vector_indexes/experience_index.pkl" ]; then
    echo -e "${RED}❌ Error: experience_index.pkl not found${NC}"
    echo "Please build the vector indexes first:"
    echo "  cd RAG"
    echo "  python build_vector_index.py"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} Vector indexes found"
echo ""

# Test 1: Import the agent
echo "----------------------------------------------------------------------"
echo "Test 1: Import main agent"
echo "----------------------------------------------------------------------"

/Users/ivanl/miniconda3/bin/conda run -p /Users/ivanl/Desktop/Development/my-awesome-agent-real/.conda --no-capture-output python -c "from app.main_agent import root_agent; print('✓ Main agent imported successfully')"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to import main agent${NC}"
    exit 1
fi

echo ""

# Test 2: Run the RAG integration test (if GEMINI_API_KEY is set)
if [ -n "$GEMINI_API_KEY" ]; then
    echo "----------------------------------------------------------------------"
    echo "Test 2: RAG Integration Test"
    echo "----------------------------------------------------------------------"
    echo ""
    
    /Users/ivanl/miniconda3/bin/conda run -p /Users/ivanl/Desktop/Development/my-awesome-agent-real/.conda --no-capture-output python test_rag_integration.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ All tests passed!${NC}"
        echo ""
        echo "You can now run the full agent with:"
        echo "  python run_agent.py"
    else
        echo -e "${RED}❌ RAG integration test failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Skipping RAG integration test (GEMINI_API_KEY not set)${NC}"
    echo ""
    echo -e "${GREEN}✅ Basic import test passed!${NC}"
    echo ""
    echo "To run full tests, set GEMINI_API_KEY and run again."
fi

echo ""
echo "======================================================================"
