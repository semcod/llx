"""Configuration for LLX planfile builder."""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class PlanfileConfig:
    """Configuration for planfile generation and execution."""
    
    DEFAULT_CONFIG = {
        "default_model": "openai/gpt-5.4-mini",
        "model_tiers": {
            "local": "ollama/llama2",
            "cheap": "openai/gpt-5.4-mini",
            "balanced": "openai/gpt-4o",
            "premium": "openai/gpt-4o-turbo"
        },
        "focus_areas": {
            "complexity": {
                "description": "Reduce cyclomatic complexity",
                "default_sprints": 3,
                "tasks": [
                    "Analyze complexity",
                    "Extract methods",
                    "Reduce nesting",
                    "Add tests"
                ]
            },
            "duplication": {
                "description": "Eliminate duplicate code",
                "default_sprints": 2,
                "tasks": [
                    "Find duplicates",
                    "Extract common",
                    "Create utilities"
                ]
            },
            "tests": {
                "description": "Improve test coverage",
                "default_sprints": 2,
                "tasks": [
                    "Analyze coverage",
                    "Add unit tests",
                    "Add integration tests"
                ]
            },
            "docs": {
                "description": "Improve documentation",
                "default_sprints": 1,
                "tasks": [
                    "Update README",
                    "Add examples",
                    "Create tutorials"
                ]
            }
        },
        "execution": {
            "default_dry_run": True,
            "parallel_execution": False,
            "max_parallel_tasks": 3
        }
    }
    
    def __init__(self, config_file: Optional[Path] = None):
        """Initialize configuration.
        
        Args:
            config_file: Path to config file (optional)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_file and config_file.exists():
            self.load_config(config_file)
    
    def load_config(self, config_file: Path) -> None:
        """Load configuration from file.
        
        Args:
            config_file: Path to YAML config file
        """
        with open(config_file) as f:
            user_config = yaml.safe_load(f)
        
        # Merge with defaults
        self._merge_config(self.config, user_config)
    
    def _merge_config(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Recursively merge config dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default=None):
        """Get configuration value.
        
        Args:
            key: Dot-separated key (e.g., 'model_tiers.cheap')
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def save_default_config(self, config_file: Path) -> None:
        """Save default configuration to file.
        
        Args:
            config_file: Path to save config
        """
        with open(config_file, 'w') as f:
            yaml.dump(self.DEFAULT_CONFIG, f, default_flow_style=False)
