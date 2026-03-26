#!/bin/bash
# Planfile Example Runner
# Demonstrates planfile-driven refactoring workflows

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          Planfile Example - Strategic Refactoring          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if LLX is available
if ! command -v llx &> /dev/null; then
    echo -e "${YELLOW}Warning: LLX not found in PATH. Using python -m llx${NC}"
    LLX_CMD="PYTHONPATH=/home/tom/github/semcod/llx python3 -m llx"
else
    LLX_CMD="llx"
fi

# Example 1: Basic complexity reduction
echo -e "${BLUE}Example 1: Basic Complexity Reduction${NC}"
echo "=========================================="
echo ""

# Create sample project structure
mkdir -p sample-project/src/{services,models,utils}
cat > sample-project/src/services/user_service.py << 'EOF'
class UserService:
    def __init__(self, db, cache, email_service, logger, config):
        self.db = db
        self.cache = cache
        self.email_service = email_service
        self.logger = logger
        self.config = config
    
    def process_user(self, user_id, data):
        if user_id is None:
            return None
        
        user = self.db.get_user(user_id)
        if user is None:
            return None
        
        if data.get('email') and user.email != data['email']:
            if self.validate_email(data['email']):
                user.email = data['email']
                self.email_service.send_verification(user)
        
        if data.get('name'):
            user.name = data['name']
        
        if data.get('preferences'):
            for key, value in data['preferences'].items():
                if key in user.preferences:
                    user.preferences[key] = value
        
        self.db.save_user(user)
        self.cache.invalidate(f"user:{user_id}")
        self.logger.info(f"User {user_id} updated")
        return user
    
    def validate_email(self, email):
        return '@' in email and '.' in email.split('@')[1]
EOF

echo -e "${GREEN}✓ Created sample project with complex code${NC}"
echo ""

# Generate strategy
echo -e "${BLUE}Generating complexity reduction strategy...${NC}"
eval $LLX_CMD plan generate sample-project \
    --model ollama/qwen2.5-coder:7b \
    --sprints 2 \
    --focus complexity \
    --output sample-project/strategy-complexity.yaml

echo ""
echo -e "${BLUE}Strategy generated! Reviewing...${NC}"
eval $LLX_CMD plan review sample-project/strategy-complexity.yaml sample-project

echo ""
echo -e "${YELLOW}Run dry-run to see what would be changed:${NC}"
eval $LLX_CMD plan apply sample-project/strategy-complexity.yaml sample-project --dry-run

echo ""
read -p "Press Enter to apply the strategy (or Ctrl+C to cancel)..."
echo ""

# Apply strategy
echo -e "${BLUE}Applying strategy...${NC}"
eval $LLX_CMD plan apply sample-project/strategy-complexity.yaml sample-project

echo ""
echo -e "${GREEN}✓ Strategy applied! Check sample-project/src/services/user_service.py for improvements${NC}"
echo ""

# Example 2: Duplication elimination
echo -e "${BLUE}Example 2: Duplication Elimination${NC}"
echo "===================================="
echo ""

# Create duplicated code
cat > sample-project/src/models/user.py << 'EOF'
class User:
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email
    
    def validate(self):
        if not self.name or len(self.name) < 2:
            return False
        if not self.email or '@' not in self.email:
            return False
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }
EOF

cat > sample-project/src/models/product.py << 'EOF'
class Product:
    def __init__(self, id, name, price):
        self.id = id
        self.name = name
        self.price = price
    
    def validate(self):
        if not self.name or len(self.name) < 2:
            return False
        if not self.price or self.price <= 0:
            return False
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price
        }
EOF

echo -e "${GREEN}✓ Created code with duplication patterns${NC}"
echo ""

# Generate deduplication strategy
echo -e "${BLUE}Generating deduplication strategy...${NC}"
eval $LLX_CMD plan generate sample-project \
    --model claude-sonnet-4 \
    --sprints 1 \
    --focus duplication \
    --output sample-project/strategy-dedup.yaml

echo ""
echo -e "${BLUE}Applying deduplication strategy...${NC}"
eval $LLX_CMD plan apply sample-project/strategy-dedup.yaml sample-project

echo ""
echo -e "${GREEN}✓ Deduplication applied! Check for base classes or utility functions${NC}"
echo ""

# Example 3: Test improvement
echo -e "${BLUE}Example 3: Test Coverage Improvement${NC}"
echo "========================================="
echo ""

# Create module without tests
cat > sample-project/src/utils/calculator.py << 'EOF'
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    def power(self, base, exp):
        if exp < 0:
            raise ValueError("Negative exponents not supported")
        result = 1
        for _ in range(exp):
            result *= base
        return result
EOF

echo -e "${GREEN}✓ Created module without tests${NC}"
echo ""

# Generate test strategy
echo -e "${BLUE}Generating test improvement strategy...${NC}"
eval $LLX_CMD plan generate sample-project \
    --model claude-sonnet-4 \
    --sprints 1 \
    --focus tests \
    --output sample-project/strategy-tests.yaml

echo ""
echo -e "${BLUE}Applying test strategy...${NC}"
eval $LLX_CMD plan apply sample-project/strategy-tests.yaml sample-project

echo ""
echo -e "${GREEN}✓ Tests generated! Check sample-project/tests/ directory${NC}"
echo ""

# Example 4: Using the manager script
echo -e "${BLUE}Example 4: Advanced Management with Python${NC}"
echo "=============================================="
echo ""

if command -v python3 &> /dev/null; then
    echo -e "${BLUE}Using planfile_manager.py for advanced orchestration...${NC}"
    
    # Generate strategy with Python manager
    python3 planfile_manager.py generate \
        --focus complexity \
        --sprints 3 \
        --project sample-project \
        --parallel
    
    echo ""
    echo -e "${GREEN}✓ Advanced strategy generated and executed!${NC}"
else
    echo -e "${YELLOW}Python3 not available, skipping advanced example${NC}"
fi

echo ""
echo -e "${CYAN}All examples completed!${NC}"
echo ""
echo -e "${BLUE}Generated files:${NC}"
echo "  - sample-project/strategy-complexity.yaml"
echo "  - sample-project/strategy-dedup.yaml"
echo "  - sample-project/strategy-tests.yaml"
echo "  - sample-project/.llx/ (metrics and analysis)"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Review the generated strategies"
echo "  2. Check the refactored code"
echo "  3. Run tests if they were generated"
echo "  4. Try creating your own strategy with custom focus"
echo ""
echo -e "${YELLOW}Clean up with: rm -rf sample-project${NC}"
