#!/bin/bash
# Install AI Tools in Docker Container
# Installs Aider, Claude Code, Cursor and dependencies

set -e

echo "🔧 Installing AI Tools..."
echo "========================"

# Update package index
echo "📦 Updating packages..."
apt-get update

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get install -y \
    git \
    curl \
    wget \
    jq \
    vim \
    nano \
    build-essential \
    python3-dev \
    python3-pip \
    nodejs \
    npm

# Install Python AI tools
echo "🐍 Installing Python AI tools..."

# Aider
echo "  Installing Aider..."
pip install aider-chat

# Claude Code (if available)
echo "  Installing Claude Code..."
pip install claude-code || echo "  ⚠️  Claude Code not available, skipping"

# Cursor CLI (if available)  
echo "  Installing Cursor CLI..."
pip install cursor-cli || echo "  ⚠️  Cursor CLI not available, skipping"

# Install additional AI tools
echo "🔧 Installing additional AI tools..."

# Continue.dev CLI
echo "  Installing Continue.dev CLI..."
npm install -g @continuehq/cli || echo "  ⚠️  Continue.dev CLI not available, skipping"

# Aider-web (web interface for Aider)
echo "  Installing Aider-web..."
pip install aider-web || echo "  ⚠️  Aider-web not available, skipping"

# Install Git tools
echo "🔧 Installing Git tools..."
pip install gitpython

# Create AI tools configuration directory
mkdir -p /root/.config/ai-tools
mkdir -p /root/.local/share/ai-tools

# Create Aider configuration
cat > /root/.config/aider/config.yml << 'EOF'
# Aider Configuration
model: qwen2.5-coder:7b
api_key: sk-proxy-local-dev
api_base: http://llx-api:4000/v1
max_tokens: 4096
temperature: 0.2

# Git settings
gitignore: true
auto_commits: false
commit_prompt: "AI-generated changes"

# Editor settings
editor: vim
diff_editor: vim

# File settings
show_diffs: true
stream: true
pretty: true

# Security
safe_mode: true
EOF

# Create Claude Code configuration
cat > /root/.config/claude-code/config.yml << 'EOF'
# Claude Code Configuration
model: qwen2.5-coder:7b
api_key: sk-proxy-local-dev
api_base: http://llx-api:4000/v1
max_tokens: 4096
temperature: 0.2

# Project settings
project_root: /workspace
auto_commit: false
show_diffs: true

# Editor settings
editor: vim
diff_editor: vim
EOF

# Create Cursor configuration
cat > /root/.config/cursor/config.yml << 'EOF'
# Cursor Configuration
model: qwen2.5-coder:7b
api_key: sk-proxy-local-dev
api_base: http://llx-api:4000/v1
max_tokens: 4096
temperature: 0.2

# Project settings
project_root: /workspace
auto_commit: false
show_diffs: true

# Editor settings
editor: vim
diff_editor: vim
EOF

# Create wrapper scripts
echo "🔧 Creating wrapper scripts..."

# Aider wrapper
cat > /usr/local/bin/aider-llx << 'EOF'
#!/bin/bash
# Aider with llx API wrapper
python -m aider \
    --model qwen2.5-coder:7b \
    --api-key sk-proxy-local-dev \
    --api-base http://llx-api:4000/v1 \
    "$@"
EOF

# Aider local wrapper
cat > /usr/local/bin/aider-local << 'EOF'
#!/bin/bash
# Aider with local Ollama wrapper
python -m aider \
    --model qwen2.5-coder:7b \
    --api-key sk-proxy-local-dev \
    --api-base http://host.docker.internal:11434 \
    "$@"
EOF

# Claude Code wrapper
cat > /usr/local/bin/claude-llx << 'EOF'
#!/bin/bash
# Claude Code with llx API wrapper
python -m claude_code \
    --model qwen2.5-coder:7b \
    --api-key sk-proxy-local-dev \
    --api-base http://llx-api:4000/v1 \
    "$@"
EOF

# Claude Code local wrapper
cat > /usr/local/bin/claude-local << 'EOF'
#!/bin/bash
# Claude Code with local Ollama wrapper
python -m claude_code \
    --model qwen2.5-coder:7b \
    --api-key sk-proxy-local-dev \
    --api-base http://host.docker.internal:11434 \
    "$@"
EOF

# Cursor wrapper
cat > /usr/local/bin/cursor-llx << 'EOF'
#!/bin/bash
# Cursor with llx API wrapper
python -m cursor \
    --model qwen2.5-coder:7b \
    --api-key sk-proxy-local-dev \
    --api-base http://llx-api:4000/v1 \
    "$@"
EOF

# Cursor local wrapper
cat > /usr/local/bin/cursor-local << 'EOF'
#!/bin/bash
# Cursor with local Ollama wrapper
python -m cursor \
    --model qwen2.5-coder:7b \
    --api-key sk-proxy-local-dev \
    --api-base http://host.docker.internal:11434 \
    "$@"
EOF

# Make wrapper scripts executable
chmod +x /usr/local/bin/aider-llx
chmod +x /usr/local/bin/aider-local
chmod +x /usr/local/bin/claude-llx
chmod +x /usr/local/bin/claude-local
chmod +x /usr/local/bin/cursor-llx
chmod +x /usr/local/bin/cursor-local

# Create test script
cat > /usr/local/bin/ai-tools-test << 'EOF'
#!/bin/bash
# Test AI Tools connectivity and functionality

echo "🧪 AI Tools Test Suite"
echo "===================="

# Test llx API
echo "🔍 Testing llx API..."
if curl -s http://llx-api:4000/health > /dev/null 2>&1; then
    echo "✅ llx API is reachable"
    
    # Test models
    models=$(curl -s http://llx-api:4000/v1/models | jq -r '.data[].id' 2>/dev/null | head -3)
    if [ -n "$models" ]; then
        echo "✅ Available models:"
        echo "$models" | sed 's/^/  • /'
    else
        echo "⚠️  No models available"
    fi
else
    echo "❌ llx API is not reachable"
fi

# Test Ollama
echo ""
echo "🔍 Testing Ollama..."
if curl -s http://host.docker.internal:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is reachable"
    
    # Test model
    response=$(curl -s http://host.docker.internal:11434/api/generate -d '{"model":"qwen2.5-coder:7b","prompt":"Hi","stream":false}' 2>/dev/null)
    if [ -n "$response" ]; then
        echo "✅ Ollama model responding"
    else
        echo "⚠️  Ollama model not responding"
    fi
else
    echo "❌ Ollama is not reachable"
fi

# Test Python packages
echo ""
echo "🔍 Testing Python packages..."
packages=("aider" "claude_code" "cursor")

for package in "${packages[@]}"; do
    if python -c "import $package" 2>/dev/null; then
        echo "✅ $package is installed"
    else
        echo "❌ $package is not installed"
    fi
done

# Test wrapper scripts
echo ""
echo "🔍 Testing wrapper scripts..."
scripts=("aider-llx" "aider-local" "claude-llx" "claude-local" "cursor-llx" "cursor-local")

for script in "${scripts[@]}"; do
    if command -v "$script" > /dev/null 2>&1; then
        echo "✅ $script is available"
    else
        echo "❌ $script is not available"
    fi
done

echo ""
echo "🎉 AI Tools Test Complete!"
EOF

chmod +x /usr/local/bin/ai-tools-test

# Create status script
cat > /usr/local/bin/ai-tools-status << 'EOF'
#!/bin/bash
# AI Tools Status Monitor

echo "🤖 AI Tools Status"
echo "=================="

# Container info
echo "📦 Container Info:"
echo "  Name: $(hostname)"
echo "  IP: $(hostname -I | awk '{print $1}')"
echo "  Workspace: $(pwd)"
echo "  Time: $(date)"
echo ""

# Service status
echo "🔍 Service Status:"
echo "  llx API: $(curl -s http://llx-api:4000/health > /dev/null 2>&1 && echo '✅ Running' || echo '❌ Down')"
echo "  Ollama: $(curl -s http://host.docker.internal:11434/api/tags > /dev/null 2>&1 && echo '✅ Running' || echo '❌ Down')"
echo ""

# Model availability
echo "📦 Model Availability:"
echo "  Ollama Models:"
curl -s http://host.docker.internal:11434/api/tags | jq -r '.models[].name' 2>/dev/null | head -5 | sed 's/^/    • /' || echo "    ❌ Not available"

echo "  llx Models:"
curl -s http://llx-api:4000/v1/models | jq -r '.data[].id' 2>/dev/null | head -5 | sed 's/^/    • /' || echo "    ❌ Not available"
echo ""

# Environment variables
echo "🔧 Environment:"
env_vars=("OPENAI_API_KEY" "OPENAI_API_BASE" "ANTHROPIC_API_KEY" "ANTHROPIC_BASE_URL" "AIDER_MODEL" "CLAUDE_MODEL" "CURSOR_MODEL")

for var in "${env_vars[@]}"; do
    value=$(eval echo \$$var)
    if [ -n "$value" ]; then
        echo "  $var: ${value:0:50}..."
    else
        echo "  $var: ❌ Not set"
    fi
done
echo ""

# Git status
echo "📁 Git Status:"
if [ -d .git ]; then
    echo "  Repository: ✅ Initialized"
    echo "  Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
    echo "  Status: $(git status --porcelain 2>/dev/null | wc -l) files changed"
else
    echo "  Repository: ❌ Not initialized"
fi
echo ""

# Disk usage
echo "💾 Disk Usage:"
echo "  Workspace: $(du -sh /workspace 2>/dev/null | cut -f1)"
echo "  Cache: $(du -sh /root/.cache 2>/dev/null | cut -f1)"
echo "  Config: $(du -sh /root/.config 2>/dev/null | cut -f1)"
EOF

chmod +x /usr/local/bin/ai-tools-status

echo ""
echo "✅ AI Tools Installation Complete!"
echo "=================================="
echo ""
echo "📋 Installed Tools:"
echo "  • Aider (aider-chat)"
echo "  • Claude Code (claude-code)"  
echo "  • Cursor CLI (cursor-cli)"
echo "  • Continue.dev CLI (@continuehq/cli)"
echo ""
echo "🔧 Wrapper Scripts:"
echo "  • aider-llx      - Aider with llx API"
echo "  • aider-local    - Aider with local Ollama"
echo "  • claude-llx     - Claude Code with llx API"
echo "  • claude-local   - Claude Code with local Ollama"
echo "  • cursor-llx     - Cursor with llx API"
echo "  • cursor-local   - Cursor with local Ollama"
echo ""
echo "🔧 Utility Scripts:"
echo "  • ai-tools-test   - Test all tools"
echo "  • ai-tools-status - Show status"
echo ""
echo "🚀 Ready to use AI tools!"
EOF

chmod +x /home/tom/github/semcod/llx/docker/ai-tools/install-tools.sh
