# VS Code + RooCode + llx Integration Example

This example demonstrates how to use RooCode extension in VS Code with llx proxy and local Ollama models for AI-powered development.

## 🎯 What it provides

1. **RooCode Extension**: Advanced AI assistant for VS Code
2. **llx Integration**: Seamless connection to local models
3. **Auto-installation**: Extensions and configurations
4. **Multiple Providers**: llx API and direct Ollama
5. **Rich Features**: Chat, inline suggestions, code actions

## 🏗️ Architecture

```
VS Code (localhost:8080)
├── RooCode Extension
├── llx API Connection (localhost:4000)
├── Local Ollama Fallback (localhost:11434)
└── AI Tools Container (optional)
```

## 🚀 Quick Start

### 1. Start Development Environment
```bash
# Start llx stack with VS Code
./docker-manage.sh dev
```

### 2. Access VS Code
```bash
# Open VS Code in browser
open http://localhost:8080
# Login with password: proxym-vscode
```

### 3. Use RooCode
VS Code will automatically:
- Install RooCode extension
- Configure llx connection
- Set up shortcuts and tasks

## 🤖 RooCode Features

### Chat Interface
- **Shortcut**: `Ctrl+Shift+R`
- **Position**: Right panel (configurable)
- **History**: Preserved conversations
- **Models**: qwen2.5-coder:7b (default)

### Inline Suggestions
- **Shortcut**: `Ctrl+Shift+I` (toggle)
- **Trigger**: Automatic (configurable)
- **Max suggestions**: 3
- **Delay**: 500ms

### Code Actions
- **Explain Code**: `Ctrl+Shift+E`
- **Refactor**: `Ctrl+Shift+F`
- **Generate Code**: `Ctrl+Shift+G`
- **Fix Bugs**: Right-click menu
- **Add Comments**: Right-click menu
- **Write Tests**: Right-click menu

## 🔧 Configuration

### RooCode Settings
```json
{
  "roocode.enable": true,
  "roocode.defaultProvider": "openai-compatible",
  "roocode.model": "qwen2.5-coder:7b",
  "roocode.apiKey": "sk-proxy-local-dev",
  "roocode.apiBaseUrl": "http://localhost:4000/v1",
  "roocode.fallbackProvider": "ollama",
  "roocode.fallbackBaseUrl": "http://localhost:11434"
}
```

### Available Models
- **qwen2.5-coder:7b** - Primary model (6GB, code specialist)
- **phi3:3.8b** - Fast model (2.2GB)
- **llama3.2:3b** - Balanced model (2.0GB)
- **deepseek-coder:1.3b** - Lightweight model (776MB)

## 📋 Usage Examples

### 1. Code Generation
```python
# In VS Code, press Ctrl+Shift+G
# Prompt: "Create a function that calculates factorial"

def factorial(n):
    """Calculate factorial of a number."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)
```

### 2. Code Explanation
```python
# Select code and press Ctrl+Shift+E
# RooCode will explain what the code does
```

### 3. Refactoring
```python
# Select function and press Ctrl+Shift+F
# Prompt: "Optimize for performance and add type hints"
```

### 4. Bug Fixing
```python
# Right-click → "Fix Bugs with AI"
# RooCode will identify and fix issues
```

### 5. Test Generation
```python
# Right-click → "Write Tests with AI"
# RooCode will generate comprehensive tests
```

## 🔄 Workflow Integration

### Daily Development
```bash
# 1. Start environment
./docker-manage.sh dev

# 2. Open VS Code
# http://localhost:8080 (password: proxym-vscode)

# 3. Start coding with AI assistance
# - Use Ctrl+Shift+R for chat
# - Use Ctrl+Shift+G for code generation
# - Use inline suggestions automatically
```

### Project Setup
```bash
# 1. Create new project
mkdir my-project
cd my-project

# 2. Open in VS Code
# VS Code will automatically detect and offer AI assistance

# 3. Generate project structure
# Use RooCode chat: "Create a Python project structure with tests"
```

### Code Review
```bash
# 1. Open file in VS Code
# 2. Select code or entire file
# 3. Press Ctrl+Shift+E (explain)
# 4. Press Ctrl+Shift+F (refactor)
# 5. Review AI suggestions
```

## 🎨 Advanced Features

### Custom Prompts
```python
# In RooCode chat, use specific prompts:
"Write a REST API endpoint for user management"
"Add comprehensive error handling to this function"
"Optimize this database query for better performance"
"Generate unit tests with 90% coverage"
```

### Context-Aware Suggestions
RooCode automatically considers:
- Current file content
- Project structure
- Import statements
- Function signatures
- Variable types

### Multi-file Operations
```python
# Select multiple files in explorer
# Right-click → "Generate Code with AI"
# Prompt: "Create a complete CRUD API for these models"
```

## 📊 Performance Tips

### Model Selection
- **qwen2.5-coder:7b**: Best for complex code generation
- **phi3:3.8b**: Fast for simple suggestions
- **llama3.2:3b**: Good balance for daily coding
- **deepseek-coder:1.3b**: Quick fixes and small edits

### Optimization
```json
{
  "roocode.temperature": 0.2,        // Lower for consistent output
  "roocode.maxTokens": 4096,         // Adjust based on needs
  "roocode.contextLength": 32000,    // Maximum context window
  "roocode.stream": true             // Real-time responses
}
```

## 🔍 Troubleshooting

### Common Issues

**RooCode not responding:**
```bash
# Check llx API status
curl http://localhost:4000/health

# Restart services
./docker-manage.sh restart dev vscode
```

**Extension not installed:**
```bash
# Check installed extensions
docker exec llx-vscode-dev code --list-extensions

# Manually install
docker exec llx-vscode-dev code --install-extension roocode.roocode
```

**Model not available:**
```bash
# Check Ollama models
ollama list

# Pull new model
ollama pull qwen2.5-coder:7b
```

**Connection issues:**
```bash
# Check network connectivity
docker exec llx-vscode-dev ping llx-api

# Verify API endpoints
curl http://localhost:4000/v1/models
curl http://localhost:11434/api/tags
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
./docker-manage.sh restart dev vscode

# View logs
./docker-manage.sh logs dev vscode | grep -i roocode
```

## 📚 Best Practices

### Prompt Engineering
- Be specific about requirements
- Provide context and examples
- Use consistent terminology
- Specify coding standards
- Request explanations for complex logic

### Code Quality
- Always review AI-generated code
- Add meaningful comments
- Write comprehensive tests
- Follow project conventions
- Use type hints consistently

### Security
- Review AI suggestions for vulnerabilities
- Don't expose sensitive data in prompts
- Use appropriate model for sensitive code
- Validate AI-generated inputs
- Keep API keys secure

## 🎯 Use Cases

### 1. Rapid Prototyping
```python
# Prompt: "Create a FastAPI application with user authentication"
# RooCode generates complete application structure
```

### 2. Code Migration
```python
# Select legacy code
# Prompt: "Modernize this code with Python 3.9+ features"
```

### 3. Documentation
```python
# Select function
# Prompt: "Add comprehensive docstring with examples and types"
```

### 4. Testing
```python
# Select module
# Prompt: "Write unit tests with pytest and 100% coverage"
```

### 5. Debugging
```python
# Select problematic code
# Prompt: "Identify and fix the bug in this function"
```

## 🚀 Next Steps

1. **Explore Features**: Try all RooCode shortcuts and actions
2. **Customize Settings**: Adjust models and parameters
3. **Integrate Workflow**: Add AI to your development process
4. **Share Knowledge**: Document effective prompts
5. **Extend Functionality**: Combine with AI tools container

## 📖 Additional Resources

- [RooCode Documentation](https://github.com/roocode/roocode-vscode)
- [llx Documentation](../../README.md)
- [Ollama Documentation](https://ollama.ai/documentation)
- [VS Code Code Server](https://github.com/coder/code-server)

---

**🎉 Enjoy coding with RooCode and local AI models!**
