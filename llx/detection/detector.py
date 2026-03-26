"""Project type detection for LLX."""

from pathlib import Path
from typing import Optional, Dict, Any, List
import re
import yaml
import os


class ProjectTypeDetector:
    """Detects project type from directory name and files."""
    
    def __init__(self):
        """Initialize with project types configuration."""
        config_path = Path(__file__).parent.parent / "configs" / "project_types.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
    
    def detect_from_path(self, path: Path) -> Optional[str]:
        """Detect project type from directory name."""
        name = path.name.lower()
        
        for project_type, config in self.config["project_types"].items():
            for pattern in config.get("detection_patterns", []):
                # Convert glob pattern to regex
                regex_pattern = pattern.replace("*", ".*")
                if re.match(f"^{regex_pattern}$", name):
                    return project_type
        
        return None
    
    def detect_from_files(self, path: Path) -> Optional[str]:
        """Detect project type from existing files."""
        # Check for package.json -> webapp
        if (path / "package.json").exists():
            return "webapp"
        
        # Check for setup.py with click -> cli
        if (path / "setup.py").exists():
            try:
                content = (path / "setup.py").read_text(encoding="utf-8")
                if any(keyword in content for keyword in ["click", "commander", "clap", "argparse"]):
                    return "cli"
            except:
                pass
        
        # Check for requirements.txt with web frameworks -> api
        if (path / "requirements.txt").exists():
            try:
                content = (path / "requirements.txt").read_text(encoding="utf-8")
                if any(framework in content for framework in ["fastapi", "flask", "django", "express"]):
                    return "api"
            except:
                pass
        
        # Check for model files -> ml
        model_extensions = [".pkl", ".joblib", ".h5", ".pth", ".pt", ".onnx"]
        for ext in model_extensions:
            if list(path.glob(f"**/*{ext}")):
                return "ml"
        
        # Check for data files -> data
        if (path / "data").exists() or list(path.glob("**/*.csv")) or list(path.glob("**/*.parquet")):
            return "data"
        
        return None
    
    def detect_from_config(self, path: Path) -> Optional[str]:
        """Detect project type from .llx-project-type file."""
        config_file = path / ".llx-project-type"
        if config_file.exists():
            try:
                content = config_file.read_text(encoding="utf-8").strip()
                if content in self.config["project_types"]:
                    return content
            except:
                pass
        
        return None
    
    def get_project_config(self, project_type: str) -> Dict[str, Any]:
        """Get configuration for detected project type."""
        return self.config["project_types"].get(project_type, {})
    
    def get_all_types(self) -> Dict[str, Dict[str, Any]]:
        """Get all available project types."""
        return self.config["project_types"]
    
    def detect(self, path: Path) -> str:
        """Detect project type using all methods."""
        # Priority: config > files > path > default
        type_from_config = self.detect_from_config(path)
        if type_from_config:
            return type_from_config
        
        type_from_files = self.detect_from_files(path)
        if type_from_files:
            return type_from_files
        
        type_from_path = self.detect_from_path(path)
        if type_from_path:
            return type_from_path
        
        # Default to api
        return "api"
