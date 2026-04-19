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

# Start llx stack with VS Code
./docker-manage.sh dev
```

# Open VS Code in browser
xdg-open http://localhost:8080
### 3. Use RooCode
VS Code will automatically:
- Install RooCode extension
- Configure llx connection
- Set up shortcuts and tasks

### Chat Interface
- **Shortcut**: `Ctrl+Shift+R`
- **Position**: Right panel (configurable)
- **History**: Preserved conversations
- **Models**: `balanced` (default tier)

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

### RooCode Settings
```json
{
  "roocode.enable": true,
  "roocode.defaultProvider": "openai-compatible",
  "roocode.model": "balanced",
  "roocode.apiKey": "sk-proxy-local-dev",
  "roocode.apiBaseUrl": "http://localhost:4000/v1",
  "roocode.fallbackProvider": "ollama",
  "roocode.fallbackBaseUrl": "http://localhost:11434"
}
```

### Available Models
- **balanced** - Primary model tier for general work
- **cheap** - Fast, inexpensive tier for simple tasks
- **premium** - High-quality tier for complex tasks
- **free** - Free-tier / low-cost tier for testing
- **local** - Ollama-backed tier for offline usage

# Prompt: "Create a function that calculates factorial"

def factorial(n):
    """Calculate factorial of a number."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)
```

# 1. Start environment
./docker-manage.sh dev

# 1. Create new project
mkdir my-project
cd my-project

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

### Model Selection
- **balanced**: Best default for general coding tasks
- **cheap**: Fast for simple suggestions
- **premium**: Best for complex code generation
- **free**: Good for low-cost experimentation

### Optimization
```json
{
  "roocode.temperature": 0.2,        // Lower for consistent output
  "roocode.maxTokens": 4096,         // Adjust based on needs
  "roocode.contextLength": 32000,    // Maximum context window
  "roocode.stream": true             // Real-time responses
}
```

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

# Enable debug logging
export DEBUG=true
./docker-manage.sh restart dev vscode

# View logs
./docker-manage.sh logs dev vscode | grep -i roocode
```

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

# Select legacy code
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
