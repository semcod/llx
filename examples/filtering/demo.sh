#!/bin/bash
# LLX Filtering Demo Script
# Shows various filtering options in action

echo "🎯 LLX Filtering Examples"
echo "========================"

# Create a sample Python file to work with
cat > sample.py << 'EOF'
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total

def process_order(order):
    items = order.get('items', [])
    total = calculate_total(items)
    return {
        'total': total,
        'item_count': len(items)
    }
EOF

echo -e "\n📝 Sample file created"
echo "-------------------"
cat sample.py

# Example 1: Tier-based filtering
echo -e "\n💰 Tier-based Filtering"
echo "------------------------"
echo "1. Cheap model for simple task:"
llx chat --model cheap --task quick_fix --prompt "Add type hints to this function" sample.py

echo -e "\n2. Balanced model for code review:"
llx chat --model balanced --task review --prompt "Review this code for improvements" sample.py

echo -e "\n3. Premium model for refactoring:"
llx chat --model premium --task refactor --prompt "Refactor this to be more Pythonic" sample.py

# Example 2: Provider selection
echo -e "\n🔌 Provider Selection"
echo "--------------------"
echo "1. Anthropic for documentation:"
llx chat --provider anthropic --task explain --prompt "Add docstrings to these functions" sample.py

echo -e "\n2. OpenAI for debugging:"
llx chat --provider openai --task quick_fix --prompt "Add error handling" sample.py

echo -e "\n3. OpenRouter for alternative suggestions:"
llx chat --provider openrouter --task refactor --prompt "Suggest alternative implementations" sample.py

# Example 3: Task-specific optimization
echo -e "\n🎯 Task-specific Optimization"
echo "-----------------------------"
echo "1. Refactoring task:"
llx chat --task refactor --model balanced --prompt "Improve code structure" sample.py

echo -e "\n2. Documentation task:"
llx chat --task explain --model cheap --prompt "Explain what this code does" sample.py

echo -e "\n3. Quick fix task:"
llx chat --task quick_fix --prompt "Add input validation" sample.py

# Example 4: Local vs Cloud
echo -e "\n🏠 Local vs Cloud Models"
echo "-----------------------"
echo "1. Local model (privacy-first):"
llx chat --local --prompt "Add logging to this function" sample.py

echo -e "\n2. Cloud model (more capable):"
llx chat --model balanced --prompt "Add comprehensive error handling" sample.py

# Example 5: Model aliases
echo -e "\n🏷️  Model Aliases"
echo "----------------"
echo "1. Coding specialist:"
llx chat --model coding --prompt "Optimize this algorithm" sample.py

echo -e "\n2. Fast model:"
llx chat --model fast --prompt "Quick review needed" sample.py

echo -e "\n3. Reliable model:"
llx chat --model reliable --prompt "Critical production fix" sample.py

# Example 6: Combined filters
echo -e "\n🔀 Combined Filters"
echo "------------------"
echo "1. Local + specific task:"
llx chat --local --task refactor --prompt "Make this more maintainable" sample.py

echo -e "\n2. Provider + tier + task:"
llx chat --provider anthropic --model balanced --task review --prompt "Peer review this code" sample.py

echo -e "\n3. Cost-effective with task hint:"
llx chat --model cheap --task quick_fix --prompt "Add type annotations" sample.py

# Example 7: Context-aware selection
echo -e "\n📊 Context-aware Selection"
echo "-------------------------"
echo "Analyzing project to show automatic model selection..."
llx analyze sample.py

echo -e "\nChat with auto-selected model:"
llx chat --prompt "Suggest improvements for this code" sample.py

# Example 8: Batch processing
echo -e "\n📦 Batch Processing Example"
echo "---------------------------"
echo "Processing multiple files with consistent model..."

# Create more sample files
cat > utils.py << 'EOF'
def format_currency(amount):
    return f"${amount:.2f}"

def validate_email(email):
    return '@' in email and '.' in email.split('@')[1]
EOF

cat > main.py << 'EOF'
from sample import process_order
from utils import format_currency, validate_email

def main():
    order = {
        'items': [
            {'name': 'Item 1', 'price': 10.99},
            {'name': 'Item 2', 'price': 5.99}
        ]
    }
    
    result = process_order(order)
    print(f"Total: {format_currency(result['total'])}")
    
if __name__ == "__main__":
    main()
EOF

echo "Files created: sample.py, utils.py, main.py"

# Process all Python files with cheap model
for file in *.py; do
    echo -e "\nProcessing $file with cheap model..."
    llx chat --model cheap --task quick_fix --prompt "Add proper docstrings" $file
done

# Clean up
echo -e "\n🧹 Cleaning up..."
rm -f sample.py utils.py main.py
echo "Done!"

echo -e "\n✅ Filtering demo completed!"
echo "Check the outputs above to see how different filters affect model selection and responses."
