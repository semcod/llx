#!/bin/bash
# AI Tools Entrypoint Script
# Sets up environment for Aider, Claude Code, Cursor, etc.

set -e

echo "🤖 Setting up AI Tools Environment..."
echo "=================================="

# Check if llx API is available
echo "🔍 Checking llx API..."
until curl -s http://llx-api:4000/health > /dev/null 2>&1; do
    echo "⏳ Waiting for llx API to be ready..."
    sleep 2
done
echo "✅ llx API is ready!"

# Check if Ollama is available
echo "🔍 Checking Ollama..."
until curl -s http://host.docker.internal:11434/api/tags > /dev/null 2>&1; do
    echo "⏳ Waiting for Ollama to be ready..."
    sleep 2
done
echo "✅ Ollama is ready!"

# Setup Git configuration
echo "🔧 Setting up Git configuration..."
git config --global user.name "$GIT_AUTHOR_NAME"
git config --global user.email "$GIT_AUTHOR_EMAIL"
git config --global init.defaultBranch main
git config --global pull.rebase false
git config --global safe.directory /workspace

# Create aliases for AI tools
echo "🔧 Creating AI tool aliases..."

# Aider alias
cat >> /root/.bashrc << 'EOF'

# AI Tools Aliases
alias aider='python -m aider --model qwen2.5-coder:7b --api-key sk-proxy-local-dev --api-base http://llx-api:4000/v1'
alias aider-local='python -m aider --model qwen2.5-coder:7b --api-key sk-proxy-local-dev --api-base http://host.docker.internal:11434'

# Claude Code alias  
alias claude='python -m claude_code --model qwen2.5-coder:7b --api-key sk-proxy-local-dev --api-base http://llx-api:4000/v1'
alias claude-local='python -m claude_code --model qwen2.5-coder:7b --api-key sk-proxy-local-dev --api-base http://host.docker.internal:11434'

# Cursor alias
alias cursor='python -m cursor --model qwen2.5-coder:7b --api-key sk-proxy-local-dev --api-base http://llx-api:4000/v1'
alias cursor-local='python -m cursor --model qwen2.5-coder:7b --api-key sk-proxy-local-dev --api-base http://host.docker.internal:11434'

# Utility functions
ai-status() {
    echo "🤖 AI Tools Status"
    echo "=================="
    echo "📊 llx API: $(curl -s http://llx-api:4000/health > /dev/null 2>&1 && echo '✅ Running' || echo '❌ Down')"
    echo "🦙 Ollama: $(curl -s http://host.docker.internal:11434/api/tags > /dev/null 2>&1 && echo '✅ Running' || echo '❌ Down')"
    echo "📦 Available Models:"
    curl -s http://host.docker.internal:11434/api/tags | jq -r '.models[].name' 2>/dev/null | head -5 | sed 's/^/  • /'
}

ai-test() {
    echo "🧪 Testing AI Tools..."
    echo "Testing llx API..."
    curl -s http://llx-api:4000/v1/models | jq -r '.data[0].id' 2>/dev/null || echo "❌ llx API test failed"
    
    echo "Testing Ollama..."
    curl -s http://host.docker.internal:11434/api/generate -d '{"model":"qwen2.5-coder:7b","prompt":"Hello","stream":false}' | jq -r '.response' 2>/dev/null | head -1 || echo "❌ Ollama test failed"
}

ai-chat() {
    local model="${1:-qwen2.5-coder:7b}"
    local message="${2:-Hello! Write a simple Python function.}"
    
    echo "🤖 Chat with $model"
    echo "Message: $message"
    echo "Response:"
    
    curl -s http://llx-api:4000/v1/chat/completions \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer sk-proxy-local-dev" \
        -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"$message\"}],\"max_tokens\":500}" \
        | jq -r '.choices[0].message.content' 2>/dev/null || echo "❌ Chat failed"
}

# Help function
ai-help() {
    echo "🤖 AI Tools Help"
    echo "================="
    echo "Commands:"
    echo "  aider         - Start Aider with llx API"
    echo "  aider-local   - Start Aider with local Ollama"
    echo "  claude        - Start Claude Code with llx API"  
    echo "  claude-local  - Start Claude Code with local Ollama"
    echo "  cursor        - Start Cursor with llx API"
    echo "  cursor-local  - Start Cursor with local Ollama"
    echo "  ai-status     - Check AI tools status"
    echo "  ai-test       - Test AI tools connectivity"
    echo "  ai-chat       - Quick chat test"
    echo ""
    echo "Examples:"
    echo "  aider                    # Start Aider"
    echo "  ai-chat qwen2.5-coder:7b 'Hello world'"
    echo "  ai-status               # Check status"
}

EOF

# Create AI tools workspace
mkdir -p /workspace/ai-tools-examples
cd /workspace/ai-tools-examples

# Create example files for testing
cat > hello.py << 'EOF'
def hello_world():
    """A simple hello world function."""
    print("Hello, World!")
    return "Hello, World!"

if __name__ == "__main__":
    hello_world()
EOF

cat > README.md << 'EOF'
# AI Tools Examples

This directory contains example files for testing AI tools.

## Available Tools

- **Aider**: AI pair programming tool
- **Claude Code**: Claude-based coding assistant  
- **Cursor**: AI-powered code editor

## Quick Start

1. Check status: `ai-status`
2. Test connectivity: `ai-test`
3. Start tool: `aider` or `claude` or `cursor`
4. Quick chat: `ai-chat "Write a function"`

## Examples

- `hello.py`: Simple Python function
- `README.md`: This file

Use AI tools to modify and improve these examples!
EOF

# Initialize git repo
git init
git add .
git commit -m "Initial commit - AI tools examples" || true

echo ""
echo "🎉 AI Tools Environment Ready!"
echo "================================"
echo ""
echo "📋 Available Commands:"
echo "  aider         - Start Aider with llx API"
echo "  claude        - Start Claude Code"
echo "  cursor        - Start Cursor"
echo "  ai-status     - Check status"
echo "  ai-test       - Test connectivity"
echo "  ai-chat       - Quick chat test"
echo "  ai-help       - Show help"
echo ""
echo "📁 Workspace: /workspace"
echo "📁 Examples: /workspace/ai-tools-examples"
echo ""
echo "🚀 Start using AI tools!"
echo ""

# Keep container running
exec "$@"
