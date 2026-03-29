#!/bin/bash
# Example: Using llx with pyqual for code quality automation

set -e

echo "=== LLX + Pyqual Integration Demo ==="
echo

# Ensure tools are installed
echo "1. Checking dependencies..."
command -v llx >/dev/null 2>&1 || { echo "Install llx: pip install llx[prellm]"; exit 1; }
command -v pyqual >/dev/null 2>&1 || { echo "Install pyqual: pip install pyqual"; exit 1; }
command -v code2llm >/dev/null 2>&1 || { echo "Install code2llm: pip install code2llm"; exit 1; }
command -v vallm >/dev/null 2>&1 || { echo "Install vallm: pip install vallm"; exit 1; }

echo "✓ All dependencies found"
echo

# Initialize project if needed
if [ ! -f "pyqual.yaml" ]; then
    echo "2. Creating pyqual configuration..."
    cp examples/pyqual-llx.yaml pyqual.yaml
    echo "✓ Created pyqual.yaml"
else
    echo "2. Using existing pyqual.yaml"
fi

if [ ! -f "llx.toml" ]; then
    echo "3. Initializing llx configuration..."
    llx init .
    echo "✓ Created llx.toml"
else
    echo "3. Using existing llx.toml"
fi

echo
echo "4. Running quality pipeline with LLX..."
echo "   This will:"
echo "   - Analyze code metrics with code2llm"
echo "   - Validate with vallm"
echo "   - Use LLX to select optimal model and generate fixes"
echo

# Run the pipeline
pyqual run

echo
echo "=== Demo Complete ==="
echo
echo "Check .pyqual/ directory for:"
echo "  - errors.json    (validation errors)"
echo "  - coverage.json  (test coverage)"
echo
echo "LLX selected model based on your project metrics."
echo "Review the generated fixes in the output above."
