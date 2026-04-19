# Cloud-Local Integration Examples

This directory demonstrates practical examples of combining cloud LLMs with local tools and AI assistants.

### 1. **Aider Integration**
Use Aider (AI pair programming) with LLX model selection:
```bash
# Local Aider with Ollama
llx chat --local --tool aider-local --prompt "Refactor this authentication module"

# Cloud Aider with premium model
llx chat --model premium --tool aider --prompt "Add comprehensive error handling"

# Hybrid approach
./hybrid_dev.sh execute "Review codebase for security issues" --tier premium --execute
./hybrid_dev.sh execute "Fix identified security issues" --local --execute
```

# Setup Claude Code environment
docker run -it --rm -v $(pwd):/workspace anthropic/claude-code

# Use through LLX
llx chat --provider anthropic --model balanced --tool claude-code --prompt "Migrate legacy code to modern patterns"

# Local development with cloud guidance
./hybrid_dev.sh execute "Design migration strategy" --tier premium
./hybrid_dev.sh execute "Implement migration" --local --execute
```

# Start development environment
./docker-manage.sh dev

# Use RooCode through LLX
llx chat --tool vscode --prompt "Add new feature with tests and documentation"

# Smart workflow
./hybrid_dev.sh workflow fullstack
```

# Use different tools for different phases
./hybrid_dev.sh execute "Generate API specification" --tier premium
./hybrid_dev.sh execute "Implement API endpoints" --tool aider-local --execute
./hybrid_dev.sh execute "Add tests" --tool aider --execute
./hybrid_dev.sh execute "Review and optimize" --tier premium
```

# Code review workflow
aider --message="Review this code for security vulnerabilities" .
aider --message="Add comprehensive error handling" .
aider --message="Optimize for performance" .

# Feature development
aider --message="Implement user authentication with JWT" .
aider --message="Add password reset functionality" .
aider --message="Create admin dashboard" .

# Refactoring
aider --message="Refactor to use dependency injection" .
aider --message="Extract common patterns into utilities" .
aider --message="Improve code organization" .
```

# Large-scale refactoring
claude-code "Refactor this monolith into microservices"

# Performance optimization
claude-code "Optimize database queries and add caching"

# Security hardening
claude-code "Add security best practices throughout codebase"

# Documentation generation
claude-code "Generate comprehensive API documentation"
```

# Through LLX automation
llx chat --tool vscode --prompt "Generate CRUD operations for User model"
llx chat --tool vscode --prompt "Add unit tests for all service methods"
```

# Phase 1: Design with premium model
llx chat --model premium --prompt "Design scalable API architecture" --save ./design/api-architecture.md

# Phase 2: Implement with Aider
aider --message="Implement API based on design/api-architecture.md" .

# Phase 3: Test with local model
llx chat --local --prompt "Generate comprehensive tests" --execute

# Phase 4: Review with premium model
llx chat --model premium --prompt "Review implementation and suggest improvements"
```

# Generate multiple components simultaneously
llx chat --model balanced --prompt "Create user service" --output services/user &
llx chat --model balanced --prompt "Create product service" --output services/product &
llx chat --model balanced --prompt "Create order service" --output services/order &
wait

# Integrate with Aider
aider --message="Integrate all services and add API gateway" .
```

# Aider for code implementation
aider --message="Implement business logic and algorithms" .

# Claude Code for architecture
claude-code "Review and improve system architecture"

# Local models for quick fixes
llx chat --local --prompt "Fix typos and formatting issues" --execute

# Premium models for complex decisions
llx chat --model premium --prompt "Resolve architectural conflicts and make design decisions"
```

# Complete e-commerce development using multiple tools

echo "🏗️  Phase 1: Architecture Design (Premium Cloud)"
llx chat --model premium --prompt """
Design complete e-commerce platform architecture:
- Microservices for users, products, orders, payments
- Event-driven architecture with Kafka
- CQRS pattern for read/write separation
- Redis caching layer
- PostgreSQL for persistence
- React frontend with Next.js
""" --save ./architecture.md

echo "🔧 Phase 2: Service Implementation (Aider)"
# Implement core services
services=("user-service" "product-service" "order-service" "payment-service")
for service in "${services[@]}"; do
    mkdir -p services/$service
    cd services/$service
    aider --message="Implement $service based on architecture.md" ../../
    cd - > /dev/null
done

echo "🌐 Phase 3: Frontend Development (VS Code + RooCode)"
cd frontend
# Use RooCode in VS Code for frontend development
echo "Open VS Code and use RooCode to implement frontend based on architecture.md"

echo "🔒 Phase 4: Security Review (Claude Code)"
claude-code "Perform comprehensive security review of entire platform"

echo "🧪 Phase 5: Testing (Local LLX)"
for service in "${services[@]}"; do
    cd services/$service
    llx chat --local --prompt "Generate comprehensive unit and integration tests" --execute
    cd - > /dev/null
done

echo "🚀 Phase 6: Deployment Setup"
llx chat --model balanced --prompt "Create Docker, Kubernetes, and CI/CD configuration" --execute
```

# ML pipeline development with hybrid approach

echo "📊 Phase 1: Pipeline Design (Premium)"
llx chat --model premium --prompt """
Design ML pipeline for fraud detection:
- Data ingestion with Apache Kafka
- Feature engineering with Spark
- Model training with scikit-learn/TensorFlow
- Real-time inference with FastAPI
- Model monitoring with MLflow
- A/B testing framework
""" --save ./ml-design.md

echo "🔬 Phase 2: Data Processing (Aider)"
aider --message="Implement data processing pipeline based on ml-design.md" .

echo "🤖 Phase 3: Model Development (Claude Code)"
claude-code "Implement advanced ML models with feature engineering and hyperparameter optimization"

echo "⚡ Phase 4: API Development (Local)"
llx chat --local --prompt "Create FastAPI service for model serving" --execute

echo "📈 Phase 5: Monitoring (Balanced)"
llx chat --model balanced --prompt "Add comprehensive monitoring and logging" --execute
```

# Cross-platform mobile app development

echo "📱 Phase 1: App Design (Premium)"
llx chat --model premium --prompt """
Design fitness tracking mobile app:
- React Native for cross-platform
- Redux for state management
- Firebase for backend
- Offline-first architecture
- Social features and sharing
- Wear OS integration
""" --save ./app-design.md

echo "🎨 Phase 2: UI Implementation (VS Code + RooCode)"
# Use RooCode in VS Code for UI development
echo "Implement UI components in VS Code with RooCode"

echo "🔧 Phase 3: Business Logic (Aider)"
aider --message="Implement app business logic and state management" .

echo "🧪 Phase 4: Testing (Local)"
llx chat --local --prompt "Generate comprehensive mobile app tests" --execute

echo "📦 Phase 5: Build and Deploy (Balanced)"
llx chat --model balanced --prompt "Create build scripts and deployment configuration" --execute
```

### 1. **Tool Selection Guidelines**
- **Aider**: Best for code implementation, refactoring, and feature development
- **Claude Code**: Ideal for architecture, complex refactoring, and large-scale changes
- **VS Code + RooCode**: Great for interactive development and UI work
- **Local LLX**: Perfect for quick fixes, documentation, and privacy-sensitive tasks

# Use premium models sparingly
llx chat --model premium --prompt "Make critical architectural decisions"

# Use balanced models for most work
llx chat --model balanced --prompt "Implement features and business logic"

# Use local models for routine tasks
llx chat --local --prompt "Fix bugs, add tests, update documentation"
```

# Multi-tool review process
aider --message="Implement feature" .
llx chat --local --prompt "Review implementation for basic issues" .
claude-code "Perform deep review and optimization" .
```

# Create reusable workflows
./hybrid_dev.sh workflow fullstack    # Complete application
./hybrid_dev.sh workflow api         # REST API
./hybrid_dev.sh workflow cli         # CLI tool
./hybrid_dev.sh workflow mobile      # Mobile app
```

# Define custom tool chain for specific needs

develop_feature() {
    local feature=$1
    
    echo "🎯 Developing feature: $feature"
    
    # 1. Design phase
    llx chat --model premium --prompt "Design $feature architecture" --save ./design/$feature.md
    
    # 2. Implementation phase
    aider --message="Implement $feature based on design/$feature.md" .
    
    # 3. Testing phase
    llx chat --local --prompt "Generate tests for $feature" --execute
    
    # 4. Review phase
    claude-code "Review $feature implementation and optimize"
    
    echo "✅ Feature $feature completed"
}

# Usage
develop_feature "user-authentication"
develop_feature "payment-processing"
develop_feature "real-time-notifications"
```

### Intelligent Tool Selection
```python
#!/usr/bin/env python3
# Automatic tool selection based on task characteristics

import re
from typing import Dict, List

class ToolSelector:
    def __init__(self):
        self.tool_patterns = {
            "aider": [
                "implement", "code", "function", "class", "method",
                "refactor", "fix", "add", "create", "build"
            ],
            "claude-code": [
                "architecture", "design", "system", "optimize",
                "performance", "security", "scalable", "complex"
            ],
            "vscode": [
                "ui", "frontend", "component", "interface", "visual",
                "interactive", "debug", "explore"
            ],
            "local": [
                "test", "document", "format", "lint", "simple",
                "quick", "minor", "typo", "comment"
            ]
        }
    
    def select_tool(self, prompt: str) -> str:
        """Select best tool for the given prompt."""
        scores = {}
        
        for tool, patterns in self.tool_patterns.items():
            score = sum(1 for pattern in patterns if pattern in prompt.lower())
            if score > 0:
                scores[tool] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return "aider"  # Default
    
    def recommend_tier(self, tool: str) -> str:
        """Recommend model tier for selected tool."""
        tier_mapping = {
            "aider": "balanced",
            "claude-code": "premium",
            "vscode": "balanced",
            "local": "local"
        }
        return tier_mapping.get(tool, "balanced")

# Usage example
selector = ToolSelector()
prompt = "Implement user authentication system"
tool = selector.select_tool(prompt)
tier = selector.recommend_tier(tool)

print(f"Recommended tool: {tool}")
print(f"Recommended tier: {tier}")
```

This hybrid approach gives you the flexibility to use the right tool for each task while optimizing for cost, quality, and privacy.
