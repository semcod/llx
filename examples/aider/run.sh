#!/bin/bash
# LLX + Aider Demo Runner

set -e

# Parse arguments
RUN_TEST=false
RUN_DEMO=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --test)
            RUN_TEST=true
            RUN_DEMO=false
            shift
            ;;
        --demo)
            RUN_DEMO=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--test|--demo] [--help]"
            echo "  --test    Run integration tests"
            echo "  --demo    Run demo (default)"
            echo "  --help    Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage"
            exit 1
            ;;
    esac
done

echo "🤖 LLX + Aider Integration"
echo "========================="
echo

# Check if we're in the right directory
if [ ! -f "aider_demo.py" ]; then
    echo "❌ Error: aider_demo.py not found. Run from examples/aider directory."
    exit 1
fi

# Check virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider activating: source ../../.venv/bin/activate"
    echo
fi

# Check dependencies
echo "🔍 Checking dependencies..."
echo

# Check LLX installation
if python -c "import llx" 2>/dev/null; then
    echo "✅ LLX is installed"
else
    echo "❌ LLX not found. Install with: pip install -e ../../"
    exit 1
fi

# Check Docker
if command -v docker >/dev/null 2>&1; then
    echo "✅ Docker is available"
    USE_DOCKER=true
else
    echo "⚠️  Docker not found, will try local installation"
    USE_DOCKER=false
fi

# Check Ollama
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "⚠️  Ollama not detected. Some features may not work."
    echo "   Start with: docker run -d -p 11434:11434 ollama/ollama"
fi

echo

# Run test or demo
if [ "$RUN_TEST" = true ]; then
    echo "🧪 Running integration tests..."
    echo "==========================="
    echo
    
    if [ -f "test_integration.py" ]; then
        python test_integration.py
    else
        echo "❌ test_integration.py not found"
        exit 1
    fi
    
    echo
    echo "✅ Tests completed!"
else
    echo "🚀 Running demo..."
    echo "=================="
    echo
    
    # Run the demo
    python aider_demo.py
    
    echo
    echo "✅ Demo completed!"
fi

echo
echo "📚 Learn more:"
echo "   - Read README.md for more examples"
echo "   - Check ../../docs/aider-integration.md"
echo "   - Try MCP server: python -m llx.mcp.server"
echo "   - Run tests: ./run.sh --test"
