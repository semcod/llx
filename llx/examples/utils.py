"""
Common utilities for LLX examples.
Moved from examples/* to minimize code duplication.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

from llx.config import LlxConfig
from llx.routing.client import LlxClient, ChatMessage


# Constants for Ollama checks
OLLAMA_TIMEOUT_SECONDS = 2
OLLAMA_STATUS_OK = 200


class ExampleHelper:
    """Helper class for common example operations."""
    
    @staticmethod
    def ensure_venv() -> None:
        """Ensure virtual environment is activated."""
        if not os.environ.get("VIRTUAL_ENV"):
            print("⚠️  Warning: No virtual environment detected")
            print("   Consider activating: source .venv/bin/activate")
    
    @staticmethod
    def check_dependencies() -> Any:
        """Check required dependencies."""
        deps = {
            "llx": "LLX CLI",
            "docker": "Docker",
        }
        
        available = {}
        for cmd, name in deps.items():
            if subprocess.run(["which", cmd], capture_output=True).returncode == 0:
                available[cmd] = True
                print(f"✅ {name} is available")
            else:
                available[cmd] = False
                print(f"❌ {name} not found")
        
        return available
    
    @staticmethod
    def check_ollama() -> bool:
        """Check if Ollama is running."""
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=OLLAMA_TIMEOUT_SECONDS)
            if response.status_code == OLLAMA_STATUS_OK:
                models = response.json().get('models', [])
                print(f"✅ Ollama running with {len(models)} models")
                return True
        except:
            pass
        print("⚠️  Ollama not detected")
        return False
    
    @staticmethod
    def select_model(
        project_path: str = ".",
        prefer_local: bool = False,
        tier: Optional[str] = None,
        provider: Optional[str] = None
    ) -> str:
        """Select appropriate model based on criteria."""
        config = LlxConfig.load(project_path)
        
        if prefer_local:
            return "ollama/qwen2.5-coder:7b"
        
        if tier:
            return config.models.get(tier, config.models["balanced"]).model_id
        
        return config.models["balanced"].model_id
    
    @staticmethod
    def run_llx_chat(
        prompt: str,
        model: Optional[str] = None,
        task: str = "refactor",
        provider: Optional[str] = None,
        local: bool = False
    ) -> str:
        """Run LLX chat with given parameters."""
        cmd = ["llx", "chat"]
        
        if local:
            cmd.append("--local")
        elif model:
            cmd.extend(["--model", model])
        
        if provider:
            cmd.extend(["--provider", provider])
        
        cmd.extend(["--task", task, "--prompt", prompt])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"LLX command failed: {result.stderr}")
        
        return result.stdout
    
    @staticmethod
    def save_history(command: str, result: Any, history_file: str = ".llx_history.json"):
        """Save command to history for analysis."""
        history = []
        if os.path.exists(history_file):
            with open(history_file) as f:
                history = json.load(f)
        
        history.append({
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "success": True if result else False
        })
        
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
    
    @staticmethod
    def create_project_structure(project_type: str, name: str, base_dir: str = ".") -> Path:
        """Create standard project structure."""
        project_path = Path(base_dir) / name
        project_path.mkdir(exist_ok=True)
        
        # Create common directories
        dirs = ["src", "tests", "docs", "config"]
        if project_type in ["react", "nextjs", "vue"]:
            dirs.extend(["public", "build"])
        elif project_type in ["fastapi", "flask", "django"]:
            dirs.extend(["api", "models", "services"])
        
        for dir_name in dirs:
            (project_path / dir_name).mkdir(exist_ok=True)
        
        return project_path
    
    @staticmethod
    def get_app_template(app_type: str) -> str:
        """Get template prompt for app type."""
        templates = {
            "react": "Create a React TypeScript application with TypeScript, ESLint, Tailwind CSS, React Router, and Jest tests",
            "nextjs": "Create a Next.js 14 application with TypeScript, Tailwind CSS, App Router, and API routes",
            "fastapi": "Create a FastAPI application with SQLAlchemy, Pydantic, JWT auth, and PostgreSQL",
            "python-cli": "Create a Python CLI with Click, Rich, YAML config, and structlog logging",
            "go-api": "Create a Go REST API with Gin, GORM, JWT middleware, and Swagger docs",
            "electron": "Create an Electron desktop app with React, TypeScript, and IPC communication",
            "flutter": "Create a Flutter mobile app with BLoC pattern, API integration, and local storage"
        }
        
        return templates.get(app_type, f"Create a {app_type} application")
    
    @staticmethod
    def setup_project(project_path: Path):
        """Setup project after generation."""
        os.chdir(project_path)
        
        # Install dependencies based on project type
        if (project_path / "package.json").exists():
            subprocess.run(["npm", "install"], check=True)
        elif (project_path / "requirements.txt").exists():
            subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
        elif (project_path / "go.mod").exists():
            subprocess.run(["go", "mod", "download"], check=True)


class TaskQueue:
    """Simple task queue for batch processing."""
    
    def __init__(self, queue_file: str = ".llx_queue.txt"):
        self.queue_file = queue_file
    
    def add(self, task: str):
        """Add task to queue."""
        with open(self.queue_file, "a") as f:
            f.write(task + "\n")
    
    def process(self, budget: Optional[float] = None):
        """Process all tasks in queue."""
        if not os.path.exists(self.queue_file):
            print("No tasks in queue")
            return
        
        with open(self.queue_file) as f:
            tasks = [line.strip() for line in f if line.strip()]
        
        for task in tasks:
            print(f"Processing: {task}")
            try:
                result = ExampleHelper.run_llx_chat(task, local=True)
                print(f"✅ Completed: {task[:50]}...")
            except Exception as e:
                print(f"❌ Failed: {e}")
        
        os.remove(self.queue_file)
        print("✅ Queue processed")


class WorkflowRunner:
    """Run predefined workflows."""
    
    @staticmethod
    def run_workflow(workflow: str, project_path: str = "."):
        """Run a predefined workflow."""
        workflows = {
            "fullstack": [
                ("analyze", "Analyze project structure"),
                ("generate", "Generate full-stack app"),
                ("test", "Run tests"),
                ("deploy", "Setup deployment")
            ],
            "refactor": [
                ("analyze", "Analyze code complexity"),
                ("refactor", "Refactor high-complexity modules"),
                ("test", "Ensure tests pass"),
                ("document", "Update documentation")
            ],
            "cli": [
                ("design", "Design CLI interface"),
                ("implement", "Implement commands"),
                ("test", "Add tests"),
                ("package", "Create distribution")
            ]
        }
        
        if workflow not in workflows:
            raise ValueError(f"Unknown workflow: {workflow}")
        
        for step, description in workflows[workflow]:
            print(f"🔄 {description}")
            # Execute step using LLX
            ExampleHelper.run_llx_chat(description, local=True)
