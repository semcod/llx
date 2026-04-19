# Strategic Refactoring with Planfile + LLX

This example demonstrates how to use LLX's planfile integration to execute comprehensive refactoring strategies with intelligent model selection and cost optimization.

### Why Planfile?
- **Strategic Planning**: Define multi-sprint refactoring strategies upfront
- **Intelligent Execution**: Each task gets the optimal model based on complexity and context
- **Progress Tracking**: Built-in progress tracking and quality gates
- **Cost Control**: Budget-aware model selection with automatic tier optimization
- **Validation**: Automatic code validation with vallm integration

# Phase 1: Generate comprehensive strategy
llx plan generate . --sprints 3 --focus complexity --tier free --output refactor-strategy.yaml

# Phase 2: Review quality gates
llx plan review refactor-strategy.yaml .

# Phase 3: Execute with dry-run first
llx plan apply refactor-strategy.yaml . --dry-run

# Phase 4: Execute sprint by sprint
llx plan apply refactor-strategy.yaml . --sprint "sprint-1"
llx plan apply refactor-strategy.yaml . --sprint "sprint-2"
llx plan apply refactor-strategy.yaml . --sprint "sprint-3"
```

# Generate focused strategy for specific issues
llx plan generate . --focus duplication --sprints 2 --output dedup-strategy.yaml

# Execute with progress monitoring
llx plan apply dedup-strategy.yaml . --dry-run
llx plan apply dedup-strategy.yaml .
```

# Continuous improvement loop
while true; do
    # Analyze current state
    llx analyze . --toon-dir .code2llm > current-metrics.json
    
    # Generate targeted strategy
    llx plan generate . --model local --sprints 1 --output quick-fix.yaml
    
    # Apply fixes
    llx plan apply quick-fix.yaml .
    
    # Validate improvements
    llx analyze . --toon-dir .code2llm > new-metrics.json
    
    sleep 86400  # Daily improvement cycle
done
```

# Complete legacy modernization using planfile

echo "🔍 Phase 1: Deep Analysis"
llx analyze . --toon-dir .code2llm --task refactor > analysis-report.txt
cat analysis-report.txt

echo "📋 Phase 2: Strategy Generation"
# Generate comprehensive 4-sprint strategy
llx plan generate . \
    --model claude-opus-4 \
    --sprints 4 \
    --focus complexity \
    --output legacy-modernization.yaml

echo "👁️  Phase 3: Strategy Review"
llx plan review legacy-modernization.yaml .

echo "🎯 Phase 4: Sprint Execution"
# Execute each sprint with validation
for sprint in sprint-1 sprint-2 sprint-3 sprint-4; do
    echo "Executing $sprint..."
    llx plan apply legacy-modernization.yaml . --sprint $sprint
    
    # Validate after each sprint
    echo "Validating $sprint results..."
    llx analyze . --toon-dir .code2llm > post-$sprint-metrics.json
    
    # Run tests
    pytest tests/ --cov=src --cov-report=html
    
    read -p "Continue to next sprint? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        break
    fi
done

echo "✨ Phase 5: Final Polish"
# Generate final polish strategy
llx plan generate . \
    --model claude-sonnet-4 \
    --sprints 1 \
    --focus docs \
    --output final-polish.yaml

llx plan apply final-polish.yaml .
```

# Refactor monolith to microservices

echo "🏗️  Phase 1: Architecture Analysis"
# Analyze monolith structure
llx analyze . --task refactor --toon-dir .code2llm > monolith-analysis.txt

echo "📐 Phase 2: Microservices Design"
# Generate microservices strategy
llx plan generate . \
    --model claude-opus-4 \
    --sprints 5 \
    --focus complexity \
    --output microservices-split.yaml

echo "🔧 Phase 3: Extract Core Services"
# Extract user, product, order services
llx plan apply microservices-split.yaml . --sprint "sprint-1"  # Extract user service
llx plan apply microservices-split.yaml . --sprint "sprint-2"  # Extract product service
llx plan apply microservices-split.yaml . --sprint "sprint-3"  # Extract order service

echo "🌐 Phase 4: API Gateway Integration"
llx plan apply microservices-split.yaml . --sprint "sprint-4"  # Build API gateway

echo "📊 Phase 5: Data Migration"
llx plan apply microservices-split.yaml . --sprint "sprint-5"  # Migrate data

echo "🧪 Phase 6: Testing & Validation"
# Generate testing strategy
llx plan generate . \
    --model claude-sonnet-4 \
    --sprints 2 \
    --focus tests \
    --output integration-tests.yaml

llx plan apply integration-tests.yaml .
```

# Systematic performance optimization

echo "⚡ Phase 1: Performance Audit"
# Identify bottlenecks
llx analyze . --task quick_fix --toon-dir .code2llm > perf-audit.txt

echo "🎯 Phase 2: Optimization Strategy"
# Generate performance-focused strategy
llx plan generate . \
    --model claude-opus-4 \
    --sprints 3 \
    --focus performance \
    --output performance-optimization.yaml

echo "🚀 Phase 3: Database Optimization"
llx plan apply performance-optimization.yaml . --sprint "sprint-1"

echo "⚡ Phase 4: Algorithm Optimization"
llx plan apply performance-optimization.yaml . --sprint "sprint-2"

echo "🔄 Phase 5: Caching & Async"
llx plan apply performance-optimization.yaml . --sprint "sprint-3"

echo "📈 Phase 6: Benchmark Validation"
# Generate benchmark suite
llx plan generate . \
    --model claude-sonnet-4 \
    --sprints 1 \
    --output benchmark-suite.yaml

llx plan apply benchmark-suite.yaml .

# Run benchmarks
python benchmarks/run_all.py
```

# Refactor with strict budget controls

BUDGET_LIMIT=50
CURRENT_COST=0

# Generate cost-optimized strategy
llx plan generate . \
    --model qwen2.5-coder:7b \
    --sprints 5 \
    --focus complexity \
    --output budget-refactor.yaml

# Execute with cost tracking
while IFS= read -r task; do
    # Estimate cost
    COST_ESTIMATE=$(llx cost estimate --task "$task")
    
    if (( $(echo "$CURRENT_COST + $COST_ESTIMATE <= $BUDGET_LIMIT" | bc -l) )); then
        echo "Executing task: $task (Estimated cost: $COST_ESTIMATE)"
        # Execute single task
        llx plan apply budget-refactor.yaml . --task "$task"
        CURRENT_COST=$(echo "$CURRENT_COST + $COST_ESTIMATE" | bc -l)
    else
        echo "Budget limit reached. Stopping."
        break
    fi
done < budget-refactor.yaml
```

# Refactor until quality gates pass

TARGET_QUALITY=90
CURRENT_QUALITY=0

while (( $(echo "$CURRENT_QUALITY < $TARGET_QUALITY" | bc -l) )); do
    echo "Current quality: $CURRENT_QUALITY%, Target: $TARGET_QUALITY%"
    
    # Generate improvement strategy
    llx plan generate . \
        --model claude-sonnet-4 \
        --sprints 1 \
        --focus quality \
        --output quality-improvement.yaml
    
    # Execute improvements
    llx plan apply quality-improvement.yaml .
    
    # Measure quality
    CURRENT_QUALITY=$(vallm measure --path . --format json | jq '.overall_score')
    
    if (( $(echo "$CURRENT_QUALITY >= $TARGET_QUALITY" | bc -l) )); then
        echo "Quality target achieved!"
        break
    fi
done
```

# Generate strategy with parallelizable sprints
llx plan generate . \
    --model claude-opus-4 \
    --sprints 4 \
    --focus complexity \
    --output parallel-refactor.yaml

# Extract independent sprints
extract_sprint() {
    local sprint_id=$1
    yq eval ".sprints[] | select(.id == \"$sprint_id\")" parallel-refactor.yaml > $sprint_id.yaml
    yq eval 'del(.sprints)' parallel-refactor.yaml > base.yaml
    yq eval ".sprints += [load(\"$sprint_id.yaml\")]" base.yaml > $sprint_id-full.yaml
}

# Extract sprints
extract_sprint "sprint-1"
extract_sprint "sprint-2"

# Execute in parallel
llx plan apply sprint-1-full.yaml . &
PID1=$!
llx plan apply sprint-2-full.yaml . &
PID2=$!

# Wait for completion
wait $PID1
wait $PID2

# Continue with dependent sprints
llx plan apply parallel-refactor.yaml . --sprint "sprint-3"
llx plan apply parallel-refactor.yaml . --sprint "sprint-4"
```

### Using Planfile with Claude Desktop
```json
{
  "mcpServers": {
    "llx": {
      "command": "python3",
      "args": ["-m", "llx.mcp"],
      "env": {
        "LLX_CONFIG_PATH": "/path/to/llx.toml"
      }
    }
  }
}
```

# 1. Generate strategy via MCP
planfile_generate --project_path . --model claude-opus-4 --sprints 3 --focus complexity

# 2. Review strategy
cat /tmp/strategy*.yaml | yq eval '.' -

# 3. Apply via MCP
planfile_apply --strategy_path /tmp/strategy-*.yaml --project_path . --dry_run

# 4. Execute
planfile_apply --strategy_path /tmp/strategy-*.yaml --project_path .
```

# Generate strategy
llx plan generate . --output aider-strategy.yaml

# Convert to Aider prompts
yq eval '.sprints[].task_patterns[].description' aider-strategy.yaml > aider-tasks.txt

# Execute with Aider
while IFS= read -r task; do
    aider --message="$task" .
done < aider-tasks.txt
```

# Start development environment
./docker-manage.sh dev

# Generate strategy
llx plan generate . --output vscode-strategy.yaml

# Execute sprint by sprint with VS Code
for sprint in sprint-1 sprint-2 sprint-3; do
    echo "Open VS Code for $sprint work"
    code . 
    
    # Apply changes when ready
    read -p "Press enter to apply $sprint changes..."
    llx plan apply vscode-strategy.yaml . --sprint $sprint
    
    # Review in VS Code
    read -p "Review changes in VS Code, press enter to continue..."
done
```

### Progress Tracking Dashboard
```python
#!/usr/bin/env python3
"""Track planfile execution progress"""

import json
import yaml
from datetime import datetime
from pathlib import Path

def track_progress(strategy_file: Path):
    """Generate progress report"""
    with open(strategy_file) as f:
        strategy = yaml.safe_load(f)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "strategy": strategy_file.name,
        "sprints": [],
        "overall_progress": 0
    }
    
    total_tasks = sum(len(s.get("task_patterns", [])) for s in strategy.get("sprints", []))
    completed_tasks = 0
    
    for sprint in strategy.get("sprints", []):
        sprint_progress = {
            "id": sprint["id"],
            "name": sprint["name"],
            "total_tasks": len(sprint.get("task_patterns", [])),
            "completed": 0,
            "status": "pending"
        }
        
        # Check for completion markers
        sprint_file = Path(f".llx/{sprint['id']}-completed.json")
        if sprint_file.exists():
            with open(sprint_file) as f:
                completed = json.load(f)
            sprint_progress["completed"] = completed.get("tasks", 0)
            sprint_progress["status"] = "completed" if sprint_progress["completed"] == sprint_progress["total_tasks"] else "in_progress"
            completed_tasks += sprint_progress["completed"]
        
        report["sprints"].append(sprint_progress)
    
    report["overall_progress"] = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Save report
    output = Path(".llx/progress-report.json")
    output.parent.mkdir(exist_ok=True)
    with open(output, "w") as f:
        json.dump(report, f, indent=2)
    
    return report

if __name__ == "__main__":
    import sys
    strategy = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("strategy.yaml")
    report = track_progress(strategy)
    print(f"Progress: {report['overall_progress']:.1f}%")
```

### 1. **Strategy Design**
- Start with clear objectives and success criteria
- Break down large refactoring into manageable sprints
- Include validation tasks in each sprint
- Plan for rollback points

### 2. **Model Selection**
- Use premium models for architecture and complex algorithms
- Use balanced models for feature implementation
- Use local/cheap models for boilerplate and simple fixes
- Consider model hints in strategy.yaml

### 3. **Quality Assurance**
- Always dry-run before execution
- Review generated strategy before applying
- Run tests after each sprint
- Use vallm for automated validation

### 4. **Progress Management**
- Track progress after each sprint
- Save intermediate states
- Document decisions and trade-offs
- Plan for iterative improvement

# If strategy generation fails
llx plan generate . --model local --sprints 1 --output debug-strategy.yaml

# Find last completed task
llx plan apply strategy.yaml . --sprint current --dry-run

# Edit strategy.yaml to remove completed tasks, then:
llx plan apply strategy.yaml .

# Edit strategy.yaml model_hints, then:
llx plan apply strategy.yaml .
```

This planfile integration provides a structured, strategic approach to codebase refactoring with intelligent model selection and comprehensive progress tracking.
