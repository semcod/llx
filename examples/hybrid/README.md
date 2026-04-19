# Cloud-Local Hybrid Development with LLX

This example demonstrates how to combine cloud LLMs for design/architecture with local models for implementation, creating an efficient and cost-effective development workflow.

### Why Hybrid?
- **Cost Optimization**: Use premium cloud models for complex design, cheap/local for implementation
- **Privacy**: Keep sensitive code local while leveraging cloud for guidance
- **Speed**: Quick iterations with local models, deep thinking with cloud models
- **Reliability**: Local models work offline, cloud models for complex tasks

# Phase 1: Architecture design with premium model
llx chat --model premium --task refactor --prompt "Design microservices architecture for e-commerce platform" --save ./architecture.md

# Phase 2: Implement services locally
for service in user-service product-service order-service; do
    mkdir -p $service
    llx chat --local --task quick_fix --prompt "Implement $service based on architecture.md" --output $service
done

# Phase 3: Integration with balanced model
llx chat --model balanced --task refactor --prompt "Create API gateway and service integration" --output ./gateway
```

# Continuous development loop
while true; do
    # Write code locally
    llx chat --local --prompt "Add user authentication feature" --execute
    
    # Periodic cloud review
    llx chat --model balanced --provider anthropic --task review --prompt "Review recent changes and suggest improvements" .
    
    sleep 3600  # Review every hour
done
```

# 1. Prototype with local model (fast, free)
llx chat --local --speed --prompt "Create basic CRUD interface" --execute

# 2. Refine with balanced cloud model
llx chat --model balanced --task refactor --prompt "Add proper error handling and validation" --execute

# 3. Polish with premium model
llx chat --model premium --task review --prompt "Optimize for performance and add advanced features" --execute
```

# Complete e-commerce platform using hybrid approach

echo "🏗️  Phase 1: Cloud Architecture Design"
llx chat --model premium --provider anthropic --task refactor --prompt """
Design a complete e-commerce platform architecture with:
- Microservices for users, products, orders, payments
- Event-driven architecture with Kafka
- CQRS pattern for read/write separation
- Redis for caching
- PostgreSQL for persistent storage
- React frontend with Next.js
- Docker containerization
- Kubernetes deployment
""" --save ./design/architecture.md

echo "🔧 Phase 2: Local Service Implementation"
# Implement core services locally
services=("user-service" "product-service" "order-service" "payment-service")
for service in "${services[@]}"; do
    echo "Implementing $service..."
    mkdir -p services/$service
    llx chat --local --task quick_fix --prompt """
    Implement $service in Node.js/TypeScript based on design/architecture.md:
    - Express.js with TypeScript
    - PostgreSQL integration
    - Event publishing to Kafka
    - Comprehensive error handling
    - Unit tests
    - Dockerfile
    """ --output services/$service
done

echo "🌐 Phase 3: Cloud-Optimized API Gateway"
llx chat --model balanced --provider openrouter --task refactor --prompt """
Create API gateway with:
- Request routing to microservices
- Authentication middleware (JWT)
- Rate limiting
- Request/response transformation
- Circuit breaker pattern
- Monitoring and logging
""" --output services/gateway

echo "⚛️  Phase 4: Frontend Development"
# Frontend with mixed approach
llx chat --model balanced --prompt """
Create React frontend with:
- TypeScript and Tailwind CSS
- Product catalog with search/filter
- Shopping cart functionality
- User authentication
- Order tracking
- Responsive design
""" --output frontend

echo "🔒 Phase 5: Security Review (Premium)"
llx chat --model premium --provider anthropic --task review --prompt """
Perform comprehensive security review of the entire platform:
- Authentication and authorization
- API security best practices
- Database security
- Container security
- Deployment security
- GDPR compliance
""" --save ./security/review.md

echo "🚀 Phase 6: Deployment Automation"
llx chat --local --prompt """
Create deployment scripts:
- Docker Compose for local development
- Kubernetes manifests
- CI/CD pipeline (GitHub Actions)
- Environment configuration
- Monitoring setup (Prometheus/Grafana)
""" --output deployment
```

# 1. Design architecture with premium model
llx chat --model premium --task refactor --prompt """
Design an ML pipeline for fraud detection with:
- Data ingestion with Apache Kafka
- Feature engineering with Spark
- Model training with scikit-learn/TensorFlow
- Real-time inference with FastAPI
- Model monitoring with MLflow
- A/B testing framework
- Dashboard with Streamlit
""" --save ./ml-architecture.md

# 2. Implement data processing locally
llx chat --local --prompt """
Implement data processing module:
- Apache Beam pipeline
- Data validation with Great Expectations
- Feature store implementation
- Unit tests with synthetic data
""" --output data-processing

# 3. Cloud model for complex ML code
llx chat --model premium --provider anthropic --prompt """
Implement ML model with:
- Advanced feature engineering
- Ensemble methods (XGBoost + Neural Network)
- Hyperparameter optimization with Optuna
- Model explainability with SHAP
- Online learning capability
""" --output ml-model

# 4. Local API and monitoring
llx chat --local --task quick_fix --prompt """
Create FastAPI service with:
- Model serving endpoints
- Request validation
- Performance monitoring
- Health checks
- Docker deployment
""" --output api-service
```

# Cloud design for UX/UI
llx chat --model balanced --provider anthropic --task explain --prompt """
Design mobile app UI/UX for fitness tracker:
- User flow diagrams
- Screen layouts
- Component library
- Design system
- Accessibility features
""" --save ./design/ui-design.md

# Local implementation of screens
screens=("login" "dashboard" "workout" "progress" "settings")
for screen in "${screens[@]}"; do
    llx chat --local --prompt "Implement $screen screen in Flutter based on ui-design.md" --output lib/screens/$screen
done

# Cloud optimization for performance
llx chat --model premium --task refactor --prompt """
Optimize Flutter app for:
- Performance (60fps)
- Battery efficiency
- Memory usage
- Offline support
- Background sync
""" --output lib/optimization
```

# Start with basic implementation
llx chat --local --speed --prompt "Create basic todo app" --execute

# Enhance with cloud model
llx chat --model balanced --prompt "Add advanced features: categories, filters, search" --execute

# Premium polish
llx chat --model premium --task review --prompt "Add animations, gestures, advanced UI patterns" --execute
```

# Queue tasks for batch processing with cloud models
echo "Refactor authentication module" >> ./cloud-tasks.txt
echo "Optimize database queries" >> ./cloud-tasks.txt
echo "Add comprehensive tests" >> ./cloud-tasks.txt

# Process batch with premium model
llx chat --model premium --prompt "Process all tasks in cloud-tasks.txt, generate implementations for each" --execute

# Clear processed tasks
> ./cloud-tasks.txt
```

# Use cloud only for specific complex tasks
complex_tasks=("algorithm-optimization" "security-audit" "architecture-review" "performance-tuning")

for task in "${complex_tasks[@]}"; do
    if [ -f "$task-required" ]; then
        echo "Processing $task with cloud model..."
        llx chat --model premium --prompt "Handle $task" --execute
        rm "$task-required"
    fi
done
```

# Use cloud model for complex refactoring
llx chat --model premium --provider anthropic --prompt "Plan refactoring of legacy codebase" --save ./refactor-plan.md

# Execute with Aider locally
aider --message="Implement refactor-plan.md" .

# Local review
llx chat --local --task review --prompt "Review refactored code for issues"
```

# Quick fixes with local model
llx chat --local --task quick_fix --prompt "Fix immediate bugs" --execute

# Deep refactoring with Claude Code through LLX
llx chat --provider anthropic --model premium --tool claude-code --prompt "Comprehensive codebase refactoring"
```

# Start VS Code with RooCode
./docker-manage.sh dev

# Use cloud model for complex features
llx chat --model premium --prompt "Design and implement complex feature X" --tool vscode

# Use local model for quick fixes
llx chat --local --prompt "Quick fix for minor issue" --tool vscode
```

# Set daily cost limits
export LLX_DAILY_BUDGET=10

# Use cheap models for 80% of tasks
llx chat --model cheap --task quick_fix --prompt "Add logging" --execute
llx chat --model cheap --task quick_fix --prompt "Fix typos" --execute
llx chat --model cheap --task quick_fix --prompt "Update dependencies" --execute

# Use balanced for 15% of tasks
llx chat --model balanced --task refactor --prompt "Improve code structure" --execute

# Use premium for 5% of tasks
llx chat --model premium --task review --prompt "Security audit" --execute
```

# Cache common responses
llx chat --local --prompt "Generate boilerplate code" --save ./templates/boilerplate

# Reuse templates
cp -r ./templates/boilerplate ./new-project
cd new-project
llx chat --local --prompt "Customize boilerplate for specific needs" --execute
```

# Log all LLX usage
llx_log() {
    echo "$(date): $*" >> ~/.llx/usage.log
    llx "$@"
}

# Analyze usage
cat ~/.llx/usage.log | grep "premium" | wc -l  # Premium usage count
cat ~/.llx/usage.log | grep "local" | wc -l    # Local usage count
```

# Compare quality across tiers
for tier in cheap balanced premium; do
    echo "Testing $tier tier..."
    llx chat --model $tier --prompt "Implement sorting algorithm" --output impl-$tier
    # Run tests and compare results
done
```

### 1. **Task Classification**
- **Local**: Boilerplate, simple fixes, documentation, unit tests
- **Balanced**: Refactoring, feature implementation, integration
- **Premium**: Architecture, security, performance optimization, complex algorithms

### 2. **Privacy Guidelines**
- Keep authentication, credentials, and sensitive data local
- Use cloud for generic code and patterns
- Sanitize code before sending to cloud models

### 3. **Performance Tips**
- Use local models for rapid iteration
- Batch cloud requests to reduce API calls
- Cache and reuse common patterns

### 4. **Quality Assurance**
- Always review cloud-generated code
- Run tests after each generation
- Use local models for quick validation

# If local model fails, fallback to cloud
llx chat --local --prompt "Task" || llx chat --model cheap --prompt "Task"

# If cloud is too expensive, use local
if [ $(llx cost --estimate) -gt $BUDGET ]; then
    llx chat --local --prompt "Task"
fi

# Balance quality and cost
llx chat --model balanced --prompt "Task" --quality-threshold 0.8 || llx chat --model premium --prompt "Task"
```

This hybrid approach gives you the best of both worlds: the privacy and cost-effectiveness of local models combined with the power and sophistication of cloud LLMs.
