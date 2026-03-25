# AI Tools Integration Example

This example demonstrates how to use shell-based AI tools (Aider, Claude Code, Cursor) through Docker with llx proxy and local Ollama models.

## 🎯 What it does

1. **Shell-based AI Tools**: Aider, Claude Code, Cursor in Docker
2. **Local Model Integration**: Uses local Ollama models through llx API
3. **Full Configuration**: Complete setup with aliases and utilities
4. **Git Integration**: Proper Git configuration for AI tools
5. **Testing Suite**: Comprehensive testing and status monitoring

## 🏗️ Architecture

```
Docker Network (llx-network)
├── llx-api (4000)           # LiteLLM proxy server
├── ai-tools (shell)         # AI tools environment
├── ollama (11434)           # Local LLM models (host)
└── redis (6379)             # Cache and session storage
```

## 🚀 Quick Start

### 1. Start Development Environment
```bash
# Start llx stack
./docker-manage.sh dev

# Start AI tools
./ai-tools-manage.sh start
```

### 2. Access AI Tools Shell
```bash
./ai-tools-manage.sh shell
```

### 3. Use AI Tools
```bash
# In AI tools shell:
aider-llx              # Start Aider with llx API
claude-llx             # Start Claude Code with llx API
cursor-llx             # Start Cursor with llx API

# Or use local Ollama directly:
aider-local            # Start Aider with local Ollama
claude-local           # Start Claude Code with local Ollama
cursor-local           # Start Cursor with local Ollama
```

## 🤖 Available AI Tools

### Aider
AI pair programming tool that works directly with your code.

```bash
# Basic usage
aider-llx file.py

# With specific model
aider-llx --model qwen2.5-coder:7b

# With message
aider-llx --message "Add type hints" file.py

# Local Ollama
aider-local --model phi3:3.8b
```

### Claude Code
Claude-based coding assistant for development tasks.

```bash
# Basic usage
claude-llx

# With task
claude-llx --task "Refactor this function"

# With specific model
claude-llx --model qwen2.5-coder:7b

# Local Ollama
claude-local --model llama3.2:3b
```

### Cursor
AI-powered code editor and assistant.

```bash
# Basic usage
cursor-llx

# With prompt
cursor-llx --prompt "Optimize this code"

# With specific model
cursor-llx --model qwen2.5-coder:7b

# Local Ollama
cursor-local --model deepseek-coder:1.3b
```

## 🔧 Configuration

### Environment Variables
AI tools container is pre-configured with:

```bash
# llx API Configuration
OPENAI_API_KEY=sk-proxy-local-dev
OPENAI_API_BASE=http://llx-api:4000/v1
ANTHROPIC_API_KEY=sk-proxy-local-dev
ANTHROPIC_BASE_URL=http://llx-api:4000/v1

# Tool-specific
AIDER_MODEL=qwen2.5-coder:7b
CLAUDE_MODEL=qwen2.5-coder:7b
CURSOR_MODEL=qwen2.5-coder:7b

# Local Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### Wrapper Scripts
Convenient wrapper scripts for different configurations:

```bash
# llx API (through proxy)
aider-llx, claude-llx, cursor-llx

# Local Ollama
aider-local, claude-local, cursor-local
```

## 📋 Management Commands

### AI Tools Management
```bash
./ai-tools-manage.sh start          # Start AI tools environment
./ai-tools-manage.sh stop           # Stop AI tools
./ai-tools-manage.sh restart        # Restart AI tools
./ai-tools-manage.sh shell         # Access AI tools shell
./ai-tools-manage.sh status         # Check status
./ai-tools-manage.sh logs           # View logs
./ai-tools-manage.sh test           # Test connectivity
```

### Utility Functions
```bash
# In AI tools shell:
ai-status                # Check all services status
ai-test                  # Test connectivity
ai-chat model "message"  # Quick chat test
ai-help                  # Show help
```

## 🧪 Testing

### Run the Example
```bash
cd examples/ai-tools
python main.py
```

### Manual Testing
```bash
# Test connectivity
./ai-tools-manage.sh test

# Test chat
./ai-tools-manage.sh chat qwen2.5-coder:7b "Hello world"

# Test in shell
./ai-tools-manage.sh shell
ai-status
ai-test
```

## 📦 Available Models

### Local Ollama Models
```bash
# Check available models
ollama list

# Popular models for coding:
qwen2.5-coder:7b      # 6GB, code specialist
phi3:3.8b             # 2.2GB, fast
llama3.2:3b           # 2.0GB, balanced
deepseek-coder:1.3b   # 776MB, lightweight
```

### Model Selection
```bash
# For code generation
aider-llx --model qwen2.5-coder:7b

# For quick tasks
aider-local --model phi3:3.8b

# For complex reasoning
claude-llx --model qwen2.5-coder:7b
```

## 🔄 Workflow Integration

### Git Integration
```bash
# Initialize repo with AI tools
git init my-project
cd my-project
./ai-tools-manage.sh shell
aider-llx

# AI tools will automatically:
# - Read/write files
# - Create commits
# - Manage branches
# - Handle merges
```

### Project Structure
```
my-project/
├── .git/
├── src/
│   ├── main.py
│   └── utils.py
└── README.md

# AI tools can work with entire project
aider-llx src/ --message "Add error handling"
```

### Daily Workflow
```bash
# 1. Start environment
./docker-manage.sh dev
./ai-tools-manage.sh start

# 2. Work on project
./ai-tools-manage.sh shell
cd /workspace/my-project
aider-llx

# 3. Use AI assistance
# - Ask for code reviews
# - Request refactoring
# - Generate documentation
# - Write tests

# 4. Stop when done
exit
./ai-tools-manage.sh stop
```

## 🎨 Use Cases

### Code Review
```bash
aider-llx --message "Review this code for improvements" src/
```

### Refactoring
```bash
claude-llx --task "Refactor this function to be more efficient"
```

### Documentation
```bash
cursor-llx --prompt "Add comprehensive docstrings to this module"
```

### Testing
```bash
aider-llx --message "Write unit tests for this function" file.py
```

### Debugging
```bash
claude-llx --task "Debug this issue and fix it"
```

## 🔍 Troubleshooting

### Common Issues

**Container not starting:**
```bash
# Check logs
./ai-tools-manage.sh logs

# Restart services
./ai-tools-manage.sh restart
```

**AI tools not responding:**
```bash
# Check connectivity
./ai-tools-manage.sh test

# Check status
./ai-tools-manage.sh status
```

**Model not available:**
```bash
# Check Ollama models
ollama list

# Pull new model
ollama pull qwen2.5-coder:7b
```

**Git issues:**
```bash
# Check Git configuration
git config --list

# Reset Git config in container
docker exec llx-ai-tools-dev git config --global user.name "Your Name"
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
./ai-tools-manage.sh start

# View detailed logs
./ai-tools-manage.sh logs | grep DEBUG
```

## 📚 Advanced Usage

### Custom Model Configuration
```bash
# Use specific model
aider-llx --model deepseek-coder:1.3b

# Set custom parameters
aider-llx --temperature 0.1 --max-tokens 2000
```

### Batch Operations
```bash
# Process multiple files
aider-llx file1.py file2.py file3.py

# Process entire directory
aider-llx src/ --message "Add type hints everywhere"
```

### Integration with IDEs
```bash
# Use AI tools alongside VS Code
./docker-manage.sh dev    # Start VS Code
./ai-tools-manage.sh start # Start AI tools

# Access both:
# VS Code: http://localhost:8080
# AI Tools: ./ai-tools-manage.sh shell
```

## 🎯 Best Practices

### Model Selection
- **qwen2.5-coder:7b**: Best for code generation
- **phi3:3.8b**: Fast for simple tasks
- **llama3.2:3b**: Good balance of speed/quality
- **deepseek-coder:1.3b**: Lightweight for quick edits

### Prompt Engineering
```bash
# Be specific
aider-llx --message "Add type hints to all functions in utils.py"

# Provide context
claude-llx --task "Refactor this function following PEP 8 guidelines"

# Use examples
cursor-llx --prompt "Make this function testable, like the example in docs/"
```

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-function
aider-llx --message "Implement new feature"

# Review changes
aider-llx --message "Review and improve the implementation"

# Commit changes
git add .
git commit -m "Add new feature"
```

## 🚀 Next Steps

1. **Explore Examples**: Try different AI tools and models
2. **Integrate Workflow**: Add AI tools to your daily development
3. **Customize Configuration**: Adjust models and settings
4. **Advanced Features**: Explore batch operations and automation
5. **Share Knowledge**: Document your workflows and best practices

## 📖 Additional Resources

- [Aider Documentation](https://github.com/paul-gauthier/aider)
- [Claude Code Documentation](https://docs.anthropic.com/claude/docs/claude-code)
- [Cursor Documentation](https://www.cursor.com/docs)
- [llx Documentation](../../README.md)
- [Ollama Documentation](https://ollama.ai/documentation)

---

**🎉 Enjoy using AI tools with llx and local models!**
