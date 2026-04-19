# Full-Stack Application Generation with LLX

This example demonstrates how to generate complete applications using LLX with various configurations and tools.

### 1. **Cloud LLM + Local Tools**
Generate code using cloud models but execute/build locally:
```bash
# Generate React app with cloud model
llx chat --model balanced --task refactor --prompt "Create a complete React TODO app with TypeScript, Tailwind CSS, and local storage" --output ./todo-app

# Generate backend API
llx chat --provider anthropic --model premium --prompt "Create a FastAPI backend with PostgreSQL for the TODO app" --output ./todo-app/backend
```

### 2. **One-liner App Generation**
Create complete applications in a single command:
```bash
# Generate full-stack MERN app
llx chat --model premium --task refactor --prompt "Generate a complete MERN stack blog application with authentication, CRUD operations, and responsive design" --execute

# Generate Python CLI tool
llx chat --local --task quick_fix --prompt "Create a CLI tool for managing Docker containers with commands: list, stop, start, logs" --execute --output ./docker-manager

# Generate static site
llx chat --model cheap --task explain --prompt "Create a static portfolio website using HTML, CSS, and JavaScript with dark mode toggle" --execute
```

### 3. **Hybrid Cloud-Local Approach**
Use cloud for design, local for implementation:
```bash
# Design architecture with premium model
llx chat --model premium --task refactor --prompt "Design microservices architecture for e-commerce platform" --save ./architecture.md

# Implement services locally
llx chat --local --task quick_fix --prompt "Implement user service based on architecture.md" --execute
```

### 4. **Tool-Assisted Development**
Integrate with development tools:
```bash
# Using Aider for AI-assisted coding
llx chat --provider openrouter --model balanced --prompt "Set up a new Next.js project with authentication" --tool aider

# Using Claude Code for refactoring
llx chat --provider anthropic --model premium --prompt "Refactor this legacy codebase to modern patterns" --tool claude-code

# Using local models for privacy
llx chat --local --task refactor --prompt "Add comprehensive logging to this application" --tool aider-local
```

### Generate React App
```bash
mkdir my-react-app && cd my-react-app
llx chat --model balanced --prompt "Create a React app with routing, state management, and API integration" --execute
```

### Generate Python API
```bash
mkdir my-api && cd my-api
llx chat --local --prompt "Create a FastAPI with SQLAlchemy, Pydantic models, and JWT auth" --execute
```

### Generate Full-Stack App
```bash
mkdir my-fullstack && cd my-fullstack
llx chat --model premium --task refactor --prompt "Generate a complete full-stack application with React frontend, Node.js backend, MongoDB database, and Docker deployment" --execute
```

# Use cheap models for boilerplate
llx chat --model cheap --task quick_fix --prompt "Generate CRUD operations for User model"

# Use balanced for business logic
llx chat --model balanced --task refactor --prompt "Implement payment processing logic"

# Use premium for security
llx chat --model premium --task review --prompt "Review and secure authentication system"
```

# Quick prototyping
llx chat --model cheap --speed --prompt "Create a quick prototype of dashboard with charts"

# Fast iteration
llx chat --model balanced --speed --prompt "Add real-time updates to the dashboard"
```

# Premium for architecture
llx chat --model premium --task refactor --prompt "Design scalable system architecture"

# Premium for complex features
llx chat --model premium --task refactor --prompt "Implement real-time collaboration with WebSockets"
```

# Start Aider session with LLX
llx chat --tool aider --prompt "Refactor this entire codebase to use TypeScript"

# Aider with specific model
llx chat --tool aider --model anthropic/claude-sonnet-4-20250514 --prompt "Add comprehensive test suite"
```

# Use Claude Code for complex refactoring
llx chat --tool claude-code --model premium --prompt "Migrate this monolith to microservices"

# Local Claude Code with Ollama
llx chat --tool claude-code-local --prompt "Add error handling throughout the application"
```

# Generate code in VS Code
llx chat --tool vscode --prompt "Create a new component with tests and documentation"

# Use RooCode extension
llx chat --tool roocode --prompt "Implement the remaining TODO items in this file"
```

# Generate complete platform
llx chat --model premium --task refactor --prompt """
Generate a complete e-commerce platform with:
- Next.js frontend with TypeScript
- Stripe payment integration
- Admin dashboard
- Product catalog with search
- Shopping cart and checkout
- Order tracking
- Email notifications
- Docker deployment
""" --execute
```

# Generate ML pipeline
llx chat --provider anthropic --model premium --prompt """
Create a complete ML pipeline for fraud detection:
- Data ingestion with Apache Kafka
- Processing with Pandas/NumPy
- ML model with scikit-learn
- API with FastAPI
- Monitoring with Prometheus
- Jupyter notebooks for analysis
- Docker Compose for deployment
""" --execute
```

# Generate mobile backend
llx chat --model balanced --task refactor --prompt """
Create a mobile app backend with:
- NestJS API with TypeScript
- PostgreSQL database
- Redis for caching
- Socket.io for real-time
- JWT authentication
- Push notifications
- S3 file storage
- Swagger documentation
""" --execute
```

# Design first
llx chat --model premium --task refactor --prompt "Design system architecture for [your project]" --save ./architecture.md

# Implement incrementally
llx chat --model balanced --prompt "Implement core module based on architecture.md"
```

# Boilerplate: cheap models
llx chat --model cheap --prompt "Generate basic CRUD structure"

# Business logic: balanced models
llx chat --model balanced --prompt "Implement business rules"

# Complex algorithms: premium models
llx chat --model premium --prompt "Design and implement complex algorithm"
```

# Version 1: MVP
llx chat --model cheap --speed --prompt "Create minimum viable product"

# Version 2: Add features
llx chat --model balanced --prompt "Add user authentication and profiles"

# Version 3: Polish
llx chat --model premium --prompt "Optimize performance and add advanced features"
```

# Generate with tests
llx chat --model balanced --prompt "Create component with unit tests and integration tests"

# Add documentation
llx chat --task explain --prompt "Generate comprehensive API documentation"

# Security review
llx chat --model premium --task review --prompt "Perform security review and suggest fixes"
```

# Use custom template
llx chat --template ./templates/react-ts --prompt "Create new feature using template"

# Save generated code as template
llx chat --prompt "Generate reusable component library" --save-template ./templates/ui-lib
```

# Polyglot application
llx chat --model premium --prompt """
Create a microservices application:
- Python services with FastAPI
- React frontend with TypeScript
- Go service for high-performance tasks
- Rust for critical components
- GraphQL API gateway
""" --execute
```

# Database-first approach
llx chat --model balanced --prompt """
Generate full CRUD application from database schema:
- Prisma schema for database
- Auto-generated REST API
- React frontend with forms
- Validation and error handling
- Migration scripts
""" --execute
```
