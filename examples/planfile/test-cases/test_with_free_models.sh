#!/bin/bash
# Test planfile with free LLM models
# This script demonstrates planfile functionality using free/local models

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Test directory
TEST_DIR="$SCRIPT_DIR/test-cases"
cd "$TEST_DIR"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          Testing Planfile with Free LLM Models              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if LLX is available
if ! command -v llx &> /dev/null; then
    echo -e "${YELLOW}Using python -m llx (LLX not in PATH)${NC}"
    LLX_CMD="python3 -m llx"
else
    LLX_CMD="llx"
fi

# Function to run test
run_test() {
    local test_name="$1"
    local model="$2"
    local focus="$3"
    local description="$4"
    
    echo -e "\n${BLUE}Test: $test_name${NC}"
    echo "Model: $model"
    echo "Focus: $focus"
    echo "Description: $description"
    echo "----------------------------------------"
    
    # Backup original file
    cp problematic_code.py problematic_code.py.backup
    
    # Generate strategy
    echo -e "${YELLOW}Generating strategy...${NC}"
    if $LLX_CMD plan generate . \
        --model "$model" \
        --sprints 1 \
        --focus "$focus" \
        --output "strategy-${focus}-${model##*:}.yaml" 2>/dev/null; then
        
        echo -e "${GREEN}✓ Strategy generated successfully${NC}"
        
        # Review strategy
        echo -e "\n${YELLOW}Reviewing strategy...${NC}"
        $LLX_CMD plan review "strategy-${focus}-${model##*:}.yaml" . 2>/dev/null || true
        
        # Dry run
        echo -e "\n${YELLOW}Running dry-run...${NC}"
        if $LLX_CMD plan apply "strategy-${focus}-${model##*:}.yaml" . --dry-run 2>/dev/null; then
            echo -e "${GREEN}✓ Dry-run completed${NC}"
            
            # Ask for confirmation
            echo -e "\n${YELLOW}Apply changes? (y/N)${NC}"
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                # Apply strategy
                echo -e "${YELLOW}Applying strategy...${NC}"
                if $LLX_CMD plan apply "strategy-${focus}-${model##*:}.yaml" . 2>/dev/null; then
                    echo -e "${GREEN}✓ Strategy applied successfully${NC}"
                    
                    # Show diff
                    echo -e "\n${YELLOW}Changes made:${NC}"
                    if command -v git &> /dev/null; then
                        git diff --no-index problematic_code.py.backup problematic_code.py || true
                    fi
                    
                    # Test if code still works
                    echo -e "\n${YELLOW}Testing refactored code...${NC}"
                    if python3 problematic_code.py 2>/dev/null; then
                        echo -e "${GREEN}✓ Code runs successfully after refactoring${NC}"
                    else
                        echo -e "${RED}✗ Code has errors after refactoring${NC}"
                    fi
                else
                    echo -e "${RED}✗ Failed to apply strategy${NC}"
                fi
            else
                echo -e "${YELLOW}Skipping application${NC}"
            fi
        else
            echo -e "${RED}✗ Dry-run failed${NC}"
        fi
    else
        echo -e "${RED}✗ Failed to generate strategy${NC}"
    fi
    
    # Restore original file
    mv problematic_code.py.backup problematic_code.py
    
    echo -e "\n${CYAN}Test completed${NC}"
    echo "========================================\n"
}

# Initialize git for diffs if not already initialized
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    git init -q
    git config user.email "test@example.com"
    git config user.name "Test User"
    git add . 2>/dev/null || true
fi

# Test 1: Local model for complexity reduction
echo -e "${BLUE}Checking for local models...${NC}"
if $LLX_CMD chat --local --model list 2>/dev/null | grep -q "qwen2.5\|llama\|mistral"; then
    LOCAL_MODEL="qwen2.5-coder:7b"
    run_test "Local Model - Complexity" "$LOCAL_MODEL" "complexity" "Reduce cyclomatic complexity using local model"
else
    echo -e "${YELLOW}No local models found, skipping local test${NC}"
fi

# Test 2: Free cloud model for duplication
echo -e "${BLUE}Testing with free cloud models...${NC}"
run_test "Free Model - Duplication" "google/gemini-2.0-flash-exp:free" "duplication" "Remove code duplication using free Gemini model"

# Test 3: Another free model for test generation
run_test "Free Model - Tests" "openrouter/meta-llama/llama-3.2-3b-instruct:free" "tests" "Generate unit tests using free Llama model"

# Test 4: Documentation improvement
run_test "Free Model - Documentation" "huggingface/mistral-7b-instruct-v0.3:free" "docs" "Improve documentation using free Mistral model"

# Test 5: Multi-sprint strategy with local model
if command -v $LLX_CMD &> /dev/null; then
    echo -e "\n${BLUE}Test: Multi-sprint Strategy${NC}"
    echo "Model: $LOCAL_MODEL (or available)"
    echo "Focus: comprehensive refactoring"
    echo "Description: Test multi-sprint execution"
    echo "----------------------------------------"
    
    cp problematic_code.py problematic_code.py.backup
    
    # Generate 3-sprint strategy
    echo -e "${YELLOW}Generating 3-sprint strategy...${NC}"
    if $LLX_CMD plan generate . \
        --model "${LOCAL_MODEL:-qwen2.5-coder:7b}" \
        --sprints 3 \
        --focus complexity \
        --output "multi-sprint-strategy.yaml" 2>/dev/null; then
        
        echo -e "${GREEN}✓ Multi-sprint strategy generated${NC}"
        
        # Show strategy structure
        echo -e "\n${YELLOW}Strategy structure:${NC}"
        if command -v yq &> /dev/null; then
            yq eval '.sprints[] | "Sprint \(.id): \(.name) (\(.task_patterns | length) tasks)"' multi-sprint-strategy.yaml
        else
            echo "Install yq for better formatting"
        fi
        
        # Execute first sprint only
        echo -e "\n${YELLOW}Executing first sprint...${NC}"
        if $LLX_CMD plan apply multi-sprint-strategy.yaml . --sprint "sprint-1" 2>/dev/null; then
            echo -e "${GREEN}✓ First sprint executed${NC}"
        else
            echo -e "${RED}✗ Failed to execute first sprint${NC}"
        fi
        
        # Clean up
        rm -f multi-sprint-strategy.yaml
    fi
    
    mv problematic_code.py.backup problematic_code.py
fi

# Test 6: Custom prompt test
echo -e "\n${BLUE}Test: Custom Prompt${NC}"
echo "Model: free model"
echo "Focus: custom refactoring"
echo "Description: Test with custom prompt"
echo "----------------------------------------"

cp problematic_code.py problematic_code.py.backup

# Create custom prompt
cat > custom_prompt.txt << 'EOF'
Refactor this Python code to follow SOLID principles:
1. Extract validation logic into separate classes
2. Remove duplicate code
3. Separate concerns (processing, validation, reporting)
4. Add proper error handling
5. Use dependency injection
Focus on maintainability and testability.
EOF

echo -e "${YELLOW}Generating strategy with custom prompt...${NC}"
if $LLX_CMD plan generate . \
    --model "openrouter/meta-llama/llama-3.2-3b-instruct:free" \
    --sprints 2 \
    --output "custom-strategy.yaml" 2>/dev/null; then
    
    echo -e "${GREEN}✓ Custom strategy generated${NC}"
    
    # Show first task
    echo -e "\n${YELLOW}First task preview:${NC}"
    if command -v yq &> /dev/null; then
        yq eval '.sprints[0].task_patterns[0].description' custom-strategy.yaml
    fi
    
    rm -f custom-strategy.yaml
fi

rm -f custom_prompt.txt
mv problematic_code.py.backup problematic_code.py

# Summary
echo -e "\n${CYAN}Test Summary${NC}"
echo "============"
echo "Generated strategies:"
ls -la strategy-*.yaml 2>/dev/null || echo "  No strategies generated"
echo ""
echo "Backup files:"
ls -la *.backup 2>/dev/null || echo "  No backup files"
echo ""
echo -e "${GREEN}All tests completed!${NC}"
echo ""
echo -e "${YELLOW}To clean up:${NC}"
echo "  rm -f strategy-*.yaml *.backup"
echo "  rm -rf .git"
