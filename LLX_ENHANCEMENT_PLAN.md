# LLX Enhancement Plan for Examples Refactoring

## Overview
Plan rozbudowy LLX aby wspierał uproszczone przykłady we wszystkich kategoriach.

## Required Changes in LLX

### 1. Enhanced `llx plan all` Command

#### Current Signature:
```python
def plan_all(
    description: str,
    output_dir: str = "./my-api",
    profile: str = "cheap",
    sprints: int = 8,
    focus: str = "api",
    run: bool = False,
    monitor: bool = False,
)
```

#### Enhanced Signature:
```python
def plan_all(
    description: str,
    output_dir: str = "./my-project",
    profile: str = "cheap",
    project_type: Optional[str] = None,      # NEW: Auto-detect or specify
    framework: Optional[str] = None,         # NEW: Framework to use
    sprints: Optional[int] = None,          # NEW: Override default
    focus: Optional[str] = None,            # NEW: Override default
    run: bool = False,
    monitor: bool = False,
    config_file: Optional[str] = None,      # NEW: Custom config
)
```

### 2. Project Type Configuration System

#### New File: `llx/configs/project_types.yaml`
```yaml
project_types:
  api:
    display_name: "REST API"
    default_focus: "api"
    default_sprints: 8
    default_framework: "fastapi"
    supported_frameworks: ["fastapi", "express", "flask", "django", "spring-boot"]
    detection_patterns:
      - "*-api"
      - "*api*"
      - "rest-*"
    templates:
      - strategy_template: "api_strategy"
      - code_template: "api_code"
    
  webapp:
    display_name: "Web Application"
    default_focus: "webapp"
    default_sprints: 6
    default_framework: "react"
    supported_frameworks: ["react", "vue", "nextjs", "angular", "svelte"]
    detection_patterns:
      - "*-app"
      - "*app*"
      - "web-*"
    templates:
      - strategy_template: "webapp_strategy"
      - code_template: "webapp_code"
      
  cli:
    display_name: "CLI Tool"
    default_focus: "cli"
    default_sprints: 4
    default_framework: "click"
    supported_frameworks: ["click", "commander", "clap", "argparse"]
    detection_patterns:
      - "*-cli"
      - "*cli*"
      - "tool-*"
    templates:
      - strategy_template: "cli_strategy"
      - code_template: "cli_code"
      
  data:
    display_name: "Data Processing"
    default_focus: "data"
    default_sprints: 6
    default_framework: "pandas"
    supported_frameworks: ["pandas", "polars", "spark", "dask"]
    detection_patterns:
      - "*-data*"
      - "*-pipeline*"
      - "*-analytics*"
    templates:
      - strategy_template: "data_strategy"
      - code_template: "data_code"
      
  ml:
    display_name: "Machine Learning"
    default_focus: "ml"
    default_sprints: 8
    default_framework: "scikit-learn"
    supported_frameworks: ["scikit-learn", "tensorflow", "pytorch", "xgboost"]
    detection_patterns:
      - "*-ml*"
      - "*-model*"
      - "*ml-*"
    templates:
      - strategy_template: "ml_strategy"
      - code_template: "ml_code"

# Default settings per project type
defaults:
  api:
    sprints: 8
    focus: "api"
    files: ["main.py", "models.py", "test_api.py", "Dockerfile", "docker-compose.yml", "README.md"]
  webapp:
    sprints: 6
    focus: "webapp"
    files: ["App.jsx", "package.json", "src/components/", "src/pages/", "Dockerfile"]
  cli:
    sprints: 4
    focus: "cli"
    files: ["main.py", "cli.py", "setup.py", "README.md"]
  data:
    sprints: 6
    focus: "data"
    files: ["pipeline.py", "config.yaml", "requirements.txt", "Dockerfile"]
  ml:
    sprints: 8
    focus: "ml"
    files: ["model.py", "train.py", "predict.py", "requirements.txt", "Dockerfile"]
```

### 3. Template System Enhancement

#### Enhanced `llx/configs/planfile_config.yaml`:
```yaml
# Strategy templates
strategy:
  templates:
    api_strategy: |
      Generate a comprehensive REST API strategy...
      
    webapp_strategy: |
      Generate a modern web application strategy...
      
    cli_strategy: |
      Generate a CLI tool strategy...
      
    data_strategy: |
      Generate a data processing pipeline strategy...
      
    ml_strategy: |
      Generate a machine learning model strategy...

# Code generation templates
code:
  templates:
    api_code:
      sprint_files:
        1: {file: "main.py", prompt: "..."}
        # ... existing API files
        
    webapp_code:
      sprint_files:
        1: {file: "package.json", prompt: "Generate package.json for {project_name}"}
        2: {file: "src/App.jsx", prompt: "Generate main App component"}
        3: {file: "src/index.js", prompt: "Generate entry point"}
        # ... more files
        
    cli_code:
      sprint_files:
        1: {file: "main.py", prompt: "Generate main CLI module"}
        2: {file: "cli.py", prompt: "Generate CLI interface"}
        # ... more files
        
    data_code:
      sprint_files:
        1: {file: "pipeline.py", prompt: "Generate data pipeline"}
        # ... more files
        
    ml_code:
      sprint_files:
        1: {file: "model.py", prompt: "Generate ML model"}
        # ... more files
```

### 4. Project Type Detection

#### New File: `llx/llx/detection/project_detector.py`:
```python
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import re

class ProjectTypeDetector:
    def __init__(self):
        with open("llx/configs/project_types.yaml", "r") as f:
            self.config = yaml.safe_load(f)
    
    def detect_from_path(self, path: Path) -> Optional[str]:
        """Detect project type from directory name"""
        name = path.name.lower()
        
        for project_type, config in self.config["project_types"].items():
            for pattern in config.get("detection_patterns", []):
                if re.match(pattern.replace("*", ".*"), name):
                    return project_type
        
        return None
    
    def detect_from_files(self, path: Path) -> Optional[str]:
        """Detect project type from existing files"""
        # Check for package.json -> webapp
        if (path / "package.json").exists():
            return "webapp"
        
        # Check for setup.py with click -> cli
        if (path / "setup.py").exists():
            content = (path / "setup.py").read_text()
            if "click" in content or "commander" in content:
                return "cli"
        
        # Check for requirements.txt with fastapi -> api
        if (path / "requirements.txt").exists():
            content = (path / "requirements.txt").read_text()
            if "fastapi" in content or "flask" in content:
                return "api"
        
        # Check for model files -> ml
        for ext in [".pkl", ".joblib", ".h5", ".pth"]:
            if list(path.glob(f"**/*{ext}")):
                return "ml"
        
        return None
    
    def get_project_config(self, project_type: str) -> Dict[str, Any]:
        """Get configuration for detected project type"""
        return self.config["project_types"].get(project_type, {})
```

### 5. Enhanced Command Implementation

#### Modified `llx/cli/app.py`:
```python
@plan_app.command("all")
def plan_all(
    description: str = typer.Argument(..., help="Project description"),
    output_dir: str = typer.Option("./my-project", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
    project_type: Optional[str] = typer.Option(None, "--type", "-t"),
    framework: Optional[str] = typer.Option(None, "--framework", "-f"),
    sprints: Optional[int] = typer.Option(None, "--sprints", "-s"),
    focus: Optional[str] = typer.Option(None, "--focus"),
    run: bool = typer.Option(False, "--run", "-r"),
    monitor: bool = typer.Option(False, "--monitor", "-m"),
    config_file: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Complete workflow: generate strategy, code, and optionally run."""
    
    # Detect project type if not specified
    if not project_type:
        detector = ProjectTypeDetector()
        project_type = detector.detect_from_path(Path.cwd()) or "api"
    
    # Get project configuration
    detector = ProjectTypeDetector()
    project_config = detector.get_project_config(project_type)
    
    # Set defaults from project type
    if not profile:
        profile = os.getenv("LLX_DEFAULT_PROFILE", "cheap")
    if not sprints:
        sprints = project_config.get("default_sprints", 8)
    if not focus:
        focus = project_config.get("default_focus", "api")
    if not framework:
        framework = project_config.get("default_framework")
    
    # Load custom templates if specified
    if config_file:
        # Load custom configuration
        pass
    
    # Continue with existing logic...
```

### 6. New Utility Commands

#### Add to `llx/cli/app.py`:
```python
@plan_app.command("detect")
def plan_detect(
    path: str = typer.Argument(".", help="Path to analyze")
) -> None:
    """Detect project type and show configuration."""
    from llx.detection.project_detector import ProjectTypeDetector
    
    detector = ProjectTypeDetector()
    project_path = Path(path)
    
    # Detect from path
    type_from_path = detector.detect_from_path(project_path)
    
    # Detect from files
    type_from_files = detector.detect_from_files(project_path)
    
    console.print(f"[bold]Project Detection Results[/bold]")
    console.print(f"  Path: {project_path}")
    console.print(f"  From directory name: {type_from_path or 'None'}")
    console.print(f"  From files: {type_from_files or 'None'}")
    
    final_type = type_from_files or type_from_path or "api"
    console.print(f"  [green]Detected type: {final_type}[/green]")
    
    # Show configuration
    config = detector.get_project_config(final_type)
    console.print(f"\n[bold]Configuration:[/bold]")
    console.print(f"  Default sprints: {config.get('default_sprints', 8)}")
    console.print(f"  Default focus: {config.get('default_focus', 'api')}")
    console.print(f"  Default framework: {config.get('default_framework', 'fastapi')}")
    console.print(f"  Supported frameworks: {', '.join(config.get('supported_frameworks', []))}")

@plan_app.command("types")
def plan_types() -> None:
    """List all available project types."""
    from llx.detection.project_detector import ProjectTypeDetector
    
    detector = ProjectTypeDetector()
    
    console.print("[bold]Available Project Types:[/bold]\n")
    
    for project_type, config in detector.config["project_types"].items():
        console.print(f"[cyan]{project_type}[/cyan] - {config.get('display_name', '')}")
        console.print(f"  Default sprints: {config.get('default_sprints')}")
        console.print(f"  Frameworks: {', '.join(config.get('supported_frameworks', []))}")
        console.print()
```

## Implementation Steps

### Step 1: Core Infrastructure (Day 1-2)
1. Create `project_types.yaml` configuration
2. Implement `ProjectTypeDetector`
3. Add `llx plan detect` and `llx plan types` commands
4. Write unit tests

### Step 2: Enhanced Commands (Day 3-4)
1. Modify `llx plan all` with new parameters
2. Implement project type auto-detection
3. Add template loading logic
4. Integration tests

### Step 3: Template Expansion (Day 5-7)
1. Create templates for each project type
2. Implement framework-specific variations
3. Add custom configuration support
4. End-to-end tests

### Step 4: Documentation (Day 8-9)
1. Update CLI help
2. Create migration guide
3. Document new features
4. Examples for each type

### Step 5: Examples Migration (Day 10-14)
1. Migrate 2-3 examples per day
2. Test each migration
3. Update documentation
4. Final review

## Testing Strategy

### Unit Tests
```python
# tests/test_project_detector.py
def test_detect_api_from_path():
    detector = ProjectTypeDetector()
    assert detector.detect_from_path(Path("my-api")) == "api"
    assert detector.detect_from_path(Path("rest-service")) == "api"

def test_detect_webapp_from_files():
    detector = ProjectTypeDetector()
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp).joinpath("package.json").write_text("{}")
        assert detector.detect_from_files(Path(tmp)) == "webapp"
```

### Integration Tests
```python
# tests/test_plan_all_integration.py
def test_plan_all_api():
    # Test API project generation
    result = runner.invoke(app, ["plan", "all", "Test API", "--type", "api"])
    assert result.exit_code == 0
    assert "main.py" in generated_files

def test_plan_all_webapp():
    # Test webapp project generation
    result = runner.invoke(app, ["plan", "all", "Test App", "--type", "webapp"])
    assert result.exit_code == 0
    assert "package.json" in generated_files
```

## Benefits

1. **Consistency**: All examples follow the same pattern
2. **Flexibility**: Support for multiple project types and frameworks
3. **Simplicity**: Scripts are minimal, logic in LLX
4. **Extensibility**: Easy to add new project types
5. **Maintainability**: Centralized configuration and templates

## Migration Path for Examples

### Before:
```bash
# examples/webapp-react/run.sh (50+ lines)
#!/bin/bash
# Complex setup with npm, webpack, etc.
```

### After:
```bash
# examples/webapp-react/run.sh (15 lines)
#!/bin/bash
set -e
DESCRIPTION="${1:-}"
if [ -n "$DESCRIPTION" ]; then
    llx plan all "$DESCRIPTION" --type webapp --framework react --run
else
    echo "Usage: $0 \"description\""
fi
```

This enhancement plan ensures LLX can handle all example types while maintaining simplicity and consistency.
