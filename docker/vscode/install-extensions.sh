#!/bin/bash
# Install VS Code Extensions for AI Development
# Focus on RooCode and complementary tools

set -e

echo "🔧 Installing VS Code Extensions for AI Development"
echo "=================================================="

# List of extensions to install
EXTENSIONS=(
    # Primary AI Assistant - RooCode
    "roocode.roocode"                    # RooCode AI Assistant
    
    # Alternative AI Extensions (backup options)
    "continue.continue"                  # Continue.dev AI Assistant
    "codeium.codeium"                    # Codeium AI Autocomplete
    "tabnine.tabnine-vscode"             # TabNine AI Autocomplete
    
    # Essential Development Extensions
    "ms-python.python"                   # Python Support
    "ms-python.black-formatter"          # Python Black Formatter
    "ms-python.flake8"                   # Python Linting
    "ms-python.mypy-type-checker"        # Python Type Checking
    "ms-vscode.vscode-json"              # JSON Support
    "redhat.vscode-yaml"                 # YAML Support
    "ms-vscode.vscode-docker"            # Docker Support
    "ms-vscode-remote.remote-containers" # Remote Containers
    "ms-vscode-remote.remote-ssh"        # Remote SSH
    
    # Git and Version Control
    "eamodio.gitlens"                    # GitLens (Git supercharged)
    "mhutchie.git-graph"                 # Git Graph
    "donjayamanne.githistory"            # Git History
    
    # Code Quality and Analysis
    "ms-vscode.vscode-eslint"            # ESLint
    "esbenp.prettier-vscode"             # Prettier
    "streetsidesoftware.code-spell-checker" # Spell Checker
    
    # Productivity
    "ms-vscode.vscode-keybindings"       # Keyboard Shortcuts
    "ms-vscode.vscode-markdown"          # Markdown Support
    "yzhang.markdown-all-in-one"         # Enhanced Markdown
    "shd101wyy.markdown-preview-enhanced" # Markdown Preview
    
    # Themes and Appearance
    "PKief.material-icon-theme"          # Material Icon Theme
    "zhuangtongfa.material-theme"        # Material Theme
)

echo "📦 Installing ${#EXTENSIONS[@]} extensions..."

# Function to check if extension is already installed
is_extension_installed() {
    local extension_id="$1"
    code --list-extensions | grep -q "$extension_id"
}

# Function to install extension
install_extension() {
    local extension_id="$1"
    echo "  🔧 Installing $extension_id..."
    
    if is_extension_installed "$extension_id"; then
        echo "    ✅ Already installed"
        return 0
    fi
    
    if code --install-extension "$extension_id" --force; then
        echo "    ✅ Installed successfully"
    else
        echo "    ❌ Failed to install"
        return 1
    fi
}

# Install all extensions
failed_extensions=()
successful_extensions=()

for extension in "${EXTENSIONS[@]}"; do
    if install_extension "$extension"; then
        successful_extensions+=("$extension")
    else
        failed_extensions+=("$extension")
    fi
    echo ""
done

# Summary
echo "📊 Installation Summary"
echo "======================"
echo "✅ Successfully installed: ${#successful_extensions[@]}/${#EXTENSIONS[@]}"
echo "❌ Failed to install: ${#failed_extensions[@]}"

if [ ${#failed_extensions[@]} -gt 0 ]; then
    echo ""
    echo "❌ Failed extensions:"
    for extension in "${failed_extensions[@]}"; do
        echo "  • $extension"
    done
fi

if [ ${#successful_extensions[@]} -gt 0 ]; then
    echo ""
    echo "✅ Successfully installed:"
    for extension in "${successful_extensions[@]}"; do
        echo "  • $extension"
    done
fi

# Configure RooCode specifically
echo ""
echo "🤖 Configuring RooCode..."

# Create RooCode configuration
mkdir -p /home/coder/.config/roocode
cat > /home/coder/.config/roocode/settings.json << 'EOF'
{
  "version": "1.0.0",
  "providers": {
    "llxAi": {
      "type": "openai-compatible",
      "name": "llx AI",
      "baseUrl": "http://localhost:4000/v1",
      "apiKey": "sk-proxy-local-dev",
      "models": {
        "qwen2.5-coder:7b": {
          "id": "qwen2.5-coder:7b",
          "name": "Qwen2.5 Coder 7B",
          "maxTokens": 4096,
          "contextWindow": 32000,
          "temperature": 0.2
        },
        "phi3:3.8b": {
          "id": "phi3:3.8b", 
          "name": "Phi3 3.8B",
          "maxTokens": 4096,
          "contextWindow": 4096,
          "temperature": 0.3
        },
        "llama3.2:3b": {
          "id": "llama3.2:3b",
          "name": "Llama3.2 3B", 
          "maxTokens": 4096,
          "contextWindow": 8192,
          "temperature": 0.2
        }
      }
    },
    "ollamaLocal": {
      "type": "ollama",
      "name": "Local Ollama",
      "baseUrl": "http://localhost:11434",
      "models": {
        "qwen2.5-coder:7b": {
          "id": "qwen2.5-coder:7b",
          "name": "Qwen2.5 Coder 7B",
          "maxTokens": 4096,
          "contextWindow": 32000,
          "temperature": 0.2
        }
      }
    }
  },
  "defaultProvider": "llxAi",
  "defaultModel": "qwen2.5-coder:7b",
  "fallbackProvider": "ollamaLocal",
  "fallbackModel": "qwen2.5-coder:7b",
  "chat": {
    "enabled": true,
    "position": "right",
    "size": "medium",
    "autoFocus": true,
    "preserveHistory": true,
    "maxHistoryItems": 100
  },
  "inline": {
    "enabled": true,
    "triggerMode": "automatic",
    "delay": 500,
    "maxSuggestions": 3,
    "showConfidence": true
  },
  "codeActions": {
    "enabled": true,
    "actions": [
      "generateCode",
      "refactor", 
      "explainCode",
      "addComments",
      "fixBugs",
      "writeTests",
      "optimizeCode",
      "generateDocs"
    ]
  },
  "shortcuts": {
    "chat": "ctrl+shift+r",
    "inline": "ctrl+shift+i", 
    "explain": "ctrl+shift+e",
    "refactor": "ctrl+shift+f",
    "generate": "ctrl+shift+g"
  }
}
EOF

# Create RooCode keybindings
mkdir -p /home/coder/.config/Code/User
cat >> /home/coder/.config/Code/User/keybindings.json << 'EOF'
[
  {
    "key": "ctrl+shift+r",
    "command": "roocode.openChat",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+i", 
    "command": "roocode.toggleInline",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+e",
    "command": "roocode.explainCode",
    "when": "editorTextFocus && editorHasSelection"
  },
  {
    "key": "ctrl+shift+f",
    "command": "roocode.refactorCode", 
    "when": "editorTextFocus && editorHasSelection"
  },
  {
    "key": "ctrl+shift+g",
    "command": "roocode.generateCode",
    "when": "editorTextFocus"
  }
]
EOF

echo "✅ RooCode configuration created"

# Create VS Code tasks for AI development
mkdir -p /home/coder/.vscode
cat > /home/coder/.vscode/tasks.json << 'EOF'
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start llx API",
      "type": "shell",
      "command": "python",
      "args": ["-m", "llx", "proxy", "start", "--port", "4000"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "dedicated",
        "showReuseMessage": true,
        "clear": false
      },
      "problemMatcher": []
    },
    {
      "label": "Test llx API",
      "type": "shell", 
      "command": "curl",
      "args": ["-s", "http://localhost:4000/v1/models"],
      "group": "test",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "dedicated"
      },
      "problemMatcher": []
    },
    {
      "label": "Check Ollama Models",
      "type": "shell",
      "command": "curl",
      "args": ["-s", "http://localhost:11434/api/tags"],
      "group": "test",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "dedicated"
      },
      "problemMatcher": []
    },
    {
      "label": "Start AI Tools",
      "type": "shell",
      "command": "./ai-tools-manage.sh",
      "args": ["start"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "dedicated"
      },
      "problemMatcher": []
    }
  ]
}
EOF

# Create VS Code launch configurations
cat > /home/coder/.vscode/launch.json << 'EOF'
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "llx API Debug",
      "type": "python",
      "request": "launch",
      "program": "-m",
      "args": ["llx", "proxy", "start", "--port", "4000"],
      "console": "integratedTerminal",
      "justMyCode": false,
      "env": {
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG"
      }
    }
  ]
}
EOF

echo "✅ VS Code tasks and launch configurations created"

# Test RooCode installation
echo ""
echo "🧪 Testing RooCode installation..."

if is_extension_installed "roocode.roocode"; then
    echo "✅ RooCode extension installed successfully"
    
    # Check if configuration exists
    if [ -f "/home/coder/.config/roocode/settings.json" ]; then
        echo "✅ RooCode configuration created"
    else
        echo "❌ RooCode configuration missing"
    fi
    
    # Check if llx API is accessible
    if curl -s http://localhost:4000/health > /dev/null 2>&1; then
        echo "✅ llx API is accessible"
    else
        echo "⚠️  llx API not running - start with Task: Start llx API"
    fi
    
    # Check if Ollama is accessible
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is accessible"
    else
        echo "⚠️  Ollama not running - start with: ollama serve"
    fi
    
else
    echo "❌ RooCode extension not installed"
fi

echo ""
echo "🎉 VS Code Extensions Installation Complete!"
echo "==========================================="
echo ""
echo "📋 Installed Extensions:"
echo "  • RooCode (Primary AI Assistant)"
echo "  • Continue.dev (Alternative)"
echo "  • Codeium (Autocomplete)"
echo "  • Python, Docker, Git tools"
echo "  • Productivity and themes"
echo ""
echo "🤖 RooCode Configuration:"
echo "  • Default provider: llx AI (http://localhost:4000)"
echo "  • Default model: qwen2.5-coder:7b"
echo "  • Fallback: Local Ollama (http://localhost:11434)"
echo ""
echo "⌨️  RooCode Shortcuts:"
echo "  • Ctrl+Shift+R: Open chat"
echo "  • Ctrl+Shift+I: Toggle inline suggestions"
echo "  • Ctrl+Shift+E: Explain code"
echo "  • Ctrl+Shift+F: Refactor code"
echo "  • Ctrl+Shift+G: Generate code"
echo ""
echo "🔧 VS Code Tasks Available:"
echo "  • Start llx API"
echo "  • Test llx API"
echo "  • Check Ollama Models"
echo "  • Start AI Tools"
echo ""
echo "🚀 Next Steps:"
echo "  1. Start llx API: Ctrl+Shift+P → Tasks: Start llx API"
echo "  2. Open RooCode chat: Ctrl+Shift+R"
echo "  3. Start coding with AI assistance!"
echo ""
echo "✨ Ready to use RooCode with llx and local models!"
