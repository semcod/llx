"""
Config Manager for llx
Manages llx configuration files and settings.
"""

import os
import sys
import json
import toml
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import shutil


class ConfigManager:
    """Manages llx configuration files and settings."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config_files = {
            "pyproject": "pyproject.toml",
            "env": ".env",
            "litellm": "litellm-config.yaml",
            "docker_dev": "docker-compose-dev.yml",
            "docker_prod": "docker-compose-prod.yml",
            "docker_main": "docker-compose.yml"
        }
        
        # Default configuration templates
        self.default_env_vars = {
            # API Keys
            "ANTHROPIC_API_KEY": "",
            "OPENAI_API_KEY": "",
            "GOOGLE_API_KEY": "",
            "OPENROUTER_API_KEY": "",
            
            # llx Configuration
            "LLX_LOG_LEVEL": "INFO",
            "LLX_DEBUG": "false",
            "LLX_CACHE_DIR": "./cache",
            
            # LiteLLM Proxy
            "LITELLM_PROXY_HOST": "0.0.0.0",
            "LITELLM_PROXY_PORT": "4000",
            "LITELLM_PROXY_MASTER_KEY": "sk-proxy-local-dev",
            
            # Local Ollama
            "OLLAMA_BASE_URL": "http://host.docker.internal:11434",
            
            # Redis
            "REDIS_URL": "redis://localhost:6379/0",
            
            # VS Code
            "VSCODE_PORT": "8080",
            "VSCODE_PASSWORD": "proxym-vscode",
            "VSCODE_PROJECT_PATH": "./",
            "VSCODE_WORKSPACE_NAME": "llx",
            
            # Budget and Limits
            "MONTHLY_BUDGET": "60.0",
            "DAILY_BUDGET": "2.0",
            "MAX_REQUESTS_PER_HOUR": "100"
        }
    
    def load_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        """Load configuration from file."""
        if config_type not in self.config_files:
            print(f"❌ Unknown config type: {config_type}")
            return None
        
        config_file = self.project_root / self.config_files[config_type]
        
        if not config_file.exists():
            print(f"❌ Config file not found: {config_file}")
            return None
        
        try:
            if config_file.suffix == ".toml":
                return toml.load(config_file)
            elif config_file.suffix in [".yaml", ".yml"]:
                import yaml
                with open(config_file, 'r') as f:
                    return yaml.safe_load(f)
            elif config_file.suffix == ".json":
                with open(config_file, 'r') as f:
                    return json.load(f)
            elif config_file.name == ".env":
                return self._load_env_file(config_file)
            else:
                print(f"❌ Unsupported config format: {config_file.suffix}")
                return None
                
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return None
    
    def save_config(self, config_type: str, config_data: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        if config_type not in self.config_files:
            print(f"❌ Unknown config type: {config_type}")
            return False
        
        config_file = self.project_root / self.config_files[config_type]
        
        try:
            # Create backup
            if config_file.exists():
                backup_file = config_file.with_suffix(f"{config_file.suffix}.backup")
                shutil.copy2(config_file, backup_file)
            
            # Save based on file type
            if config_file.suffix == ".toml":
                toml.dump(config_data, config_file)
            elif config_file.suffix in [".yaml", ".yml"]:
                import yaml
                with open(config_file, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            elif config_file.suffix == ".json":
                with open(config_file, 'w') as f:
                    json.dump(config_data, f, indent=2)
            elif config_file.name == ".env":
                self._save_env_file(config_file, config_data)
            else:
                print(f"❌ Unsupported config format: {config_file.suffix}")
                return False
            
            print(f"✅ Configuration saved: {config_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            return False
    
    def _load_env_file(self, env_file: Path) -> Dict[str, str]:
        """Load .env file."""
        env_vars = {}
        
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        
        return env_vars
    
    def _save_env_file(self, env_file: Path, env_vars: Dict[str, str]) -> bool:
        """Save .env file."""
        with open(env_file, 'w') as f:
            f.write("# llx Environment Configuration\n")
            f.write("# Generated by llx config manager\n\n")
            
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        return True
    
    def create_default_env(self, overwrite: bool = False) -> bool:
        """Create default .env file."""
        env_file = self.project_root / ".env"
        
        if env_file.exists() and not overwrite:
            print("⚠️  .env file already exists. Use --overwrite to replace it.")
            return False
        
        return self.save_config("env", self.default_env_vars)
    
    def update_env_var(self, key: str, value: str) -> bool:
        """Update a single environment variable."""
        env_vars = self.load_config("env") or {}
        env_vars[key] = value
        return self.save_config("env", env_vars)
    
    def get_env_var(self, key: str, default: str = None) -> Optional[str]:
        """Get environment variable value."""
        env_vars = self.load_config("env") or {}
        return env_vars.get(key, default)
    
    def validate_env_config(self) -> Dict[str, List[str]]:
        """Validate environment configuration."""
        env_vars = self.load_config("env") or {}
        issues = {
            "missing": [],
            "invalid": [],
            "warnings": []
        }
        
        # Check required variables
        required_vars = ["LITELLM_PROXY_MASTER_KEY", "OLLAMA_BASE_URL"]
        for var in required_vars:
            if not env_vars.get(var):
                issues["missing"].append(f"Missing required variable: {var}")
        
        # Validate URLs
        url_vars = ["OLLAMA_BASE_URL", "REDIS_URL"]
        for var in url_vars:
            value = env_vars.get(var)
            if value and not (value.startswith("http://") or value.startswith("redis://")):
                issues["invalid"].append(f"Invalid URL format for {var}: {value}")
        
        # Validate numeric values
        numeric_vars = ["LITELLM_PROXY_PORT", "VSCODE_PORT", "MONTHLY_BUDGET"]
        for var in numeric_vars:
            value = env_vars.get(var)
            if value:
                try:
                    float(value)
                except ValueError:
                    issues["invalid"].append(f"Invalid numeric value for {var}: {value}")
        
        # Check for potential issues
        if env_vars.get("LITELLM_PROXY_MASTER_KEY") == "sk-proxy-local-dev":
            issues["warnings"].append("Using default proxy master key (not secure for production)")
        
        return issues
    
    def get_llx_config(self) -> Optional[Dict[str, Any]]:
        """Get llx configuration from pyproject.toml."""
        config = self.load_config("pyproject")
        
        if not config:
            return None
        
        return config.get("tool", {}).get("llx", {})
    
    def update_llx_config(self, updates: Dict[str, Any]) -> bool:
        """Update llx configuration in pyproject.toml."""
        config = self.load_config("pyproject") or {}
        
        # Ensure tool.llx section exists
        if "tool" not in config:
            config["tool"] = {}
        if "llx" not in config["tool"]:
            config["tool"]["llx"] = {}
        
        # Apply updates
        config["tool"]["llx"].update(updates)
        
        return self.save_config("pyproject", config)
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration."""
        llx_config = self.get_llx_config() or {}
        return llx_config.get("models", {})
    
    def add_model(self, tier: str, model_config: Dict[str, Any]) -> bool:
        """Add or update a model configuration."""
        models = self.get_model_config()
        models[tier] = model_config
        
        return self.update_llx_config({"models": models})
    
    def remove_model(self, tier: str) -> bool:
        """Remove a model configuration."""
        models = self.get_model_config()
        
        if tier in models:
            del models[tier]
            return self.update_llx_config({"models": models})
        
        print(f"⚠️  Model tier '{tier}' not found")
        return False
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """List all configured models."""
        models = self.get_model_config()
        
        print("🤖 Configured Models:")
        print("====================")
        
        for tier, config in models.items():
            print(f"\n{tier.upper()}:")
            print(f"  Name: {config.get('name', 'Unknown')}")
            print(f"  Provider: {config.get('provider', 'Unknown')}")
            print(f"  Model ID: {config.get('model_id', 'Unknown')}")
            print(f"  Context: {config.get('max_context', 'Unknown')}")
            
            costs = config.get("costs", {})
            if costs:
                print(f"  Costs: ${costs.get('per_1k_input', 0):.4f} / ${costs.get('per_1k_output', 0):.4f} per 1K tokens")
        
        return models
    
    def backup_configs(self, backup_dir: str = None) -> bool:
        """Backup all configuration files."""
        if not backup_dir:
            backup_dir = self.project_root / "backups" / f"config-{int(time.time())}"
        
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        print(f"💾 Backing up configurations to {backup_path}")
        
        backed_up = []
        failed = []
        
        for config_type, filename in self.config_files.items():
            source_file = self.project_root / filename
            
            if source_file.exists():
                try:
                    backup_file = backup_path / filename
                    shutil.copy2(source_file, backup_file)
                    backed_up.append(filename)
                    print(f"  ✅ {filename}")
                except Exception as e:
                    failed.append((filename, str(e)))
                    print(f"  ❌ {filename}: {e}")
        
        print(f"\n📊 Backup Summary:")
        print(f"  ✅ Backed up: {len(backed_up)} files")
        print(f"  ❌ Failed: {len(failed)} files")
        
        if failed:
            print("\n❌ Failed backups:")
            for filename, error in failed:
                print(f"  • {filename}: {error}")
        
        return len(failed) == 0
    
    def restore_configs(self, backup_dir: str) -> bool:
        """Restore configuration files from backup."""
        backup_path = Path(backup_dir)
        
        if not backup_path.exists():
            print(f"❌ Backup directory not found: {backup_path}")
            return False
        
        print(f"📦 Restoring configurations from {backup_path}")
        
        restored = []
        failed = []
        
        for config_type, filename in self.config_files.items():
            backup_file = backup_path / filename
            target_file = self.project_root / filename
            
            if backup_file.exists():
                try:
                    # Create backup of current file
                    if target_file.exists():
                        current_backup = target_file.with_suffix(f"{target_file.suffix}.current")
                        shutil.copy2(target_file, current_backup)
                    
                    # Restore from backup
                    shutil.copy2(backup_file, target_file)
                    restored.append(filename)
                    print(f"  ✅ {filename}")
                except Exception as e:
                    failed.append((filename, str(e)))
                    print(f"  ❌ {filename}: {e}")
        
        print(f"\n📊 Restore Summary:")
        print(f"  ✅ Restored: {len(restored)} files")
        print(f"  ❌ Failed: {len(failed)} files")
        
        if failed:
            print("\n❌ Failed restores:")
            for filename, error in failed:
                print(f"  • {filename}: {error}")
        
        return len(failed) == 0
    
    def generate_docker_env_file(self, env: str = "dev") -> bool:
        """Generate .env file for Docker environment."""
        docker_configs = {
            "dev": {
                "COMPOSE_FILE": "docker-compose-dev.yml",
                "COMPOSE_PROJECT_NAME": "llx-dev",
                "ENVIRONMENT": "development"
            },
            "prod": {
                "COMPOSE_FILE": "docker-compose-prod.yml", 
                "COMPOSE_PROJECT_NAME": "llx-prod",
                "ENVIRONMENT": "production"
            },
            "full": {
                "COMPOSE_FILE": "docker-compose.yml",
                "COMPOSE_PROJECT_NAME": "llx-full",
                "ENVIRONMENT": "full"
            }
        }
        
        if env not in docker_configs:
            print(f"❌ Unknown environment: {env}")
            return False
        
        # Load current .env
        current_env = self.load_config("env") or {}
        
        # Add Docker-specific variables
        docker_env = docker_configs[env]
        current_env.update(docker_env)
        
        return self.save_config("env", current_env)
    
    def validate_docker_configs(self) -> Dict[str, List[str]]:
        """Validate Docker configuration files."""
        issues = {
            "missing": [],
            "invalid": [],
            "warnings": []
        }
        
        # Check required Docker files
        required_docker_files = ["docker-compose-dev.yml", "docker-compose-prod.yml"]
        
        for filename in required_docker_files:
            file_path = self.project_root / filename
            if not file_path.exists():
                issues["missing"].append(f"Missing Docker file: {filename}")
        
        # Validate Docker configurations
        for config_type in ["docker_dev", "docker_prod", "docker_main"]:
            config = self.load_config(config_type)
            
            if config:
                # Check for required services
                services = config.get("services", {})
                
                if "llx-api" not in services:
                    issues["missing"].append(f"Missing llx-api service in {config_type}")
                
                if "redis" not in services:
                    issues["warnings"].append(f"Missing redis service in {config_type}")
        
        return issues
    
    def create_profile(self, profile_name: str, config_overrides: Dict[str, str] = None) -> bool:
        """Create a configuration profile."""
        profiles_dir = self.project_root / "profiles"
        profiles_dir.mkdir(exist_ok=True)
        
        profile_file = profiles_dir / f"{profile_name}.env"
        
        # Start with default configuration
        profile_config = self.default_env_vars.copy()
        
        # Apply overrides
        if config_overrides:
            profile_config.update(config_overrides)
        
        # Save profile
        try:
            with open(profile_file, 'w') as f:
                f.write(f"# llx Profile: {profile_name}\n")
                f.write("# Generated by llx config manager\n\n")
                
                for key, value in profile_config.items():
                    f.write(f"{key}={value}\n")
            
            print(f"✅ Profile created: {profile_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating profile: {e}")
            return False
    
    def load_profile(self, profile_name: str) -> bool:
        """Load a configuration profile."""
        profile_file = self.project_root / "profiles" / f"{profile_name}.env"
        
        if not profile_file.exists():
            print(f"❌ Profile not found: {profile_name}")
            return False
        
        try:
            profile_vars = self._load_env_file(profile_file)
            return self.save_config("env", profile_vars)
            
        except Exception as e:
            print(f"❌ Error loading profile: {e}")
            return False
    
    def list_profiles(self) -> List[str]:
        """List available configuration profiles."""
        profiles_dir = self.project_root / "profiles"
        
        if not profiles_dir.exists():
            return []
        
        profiles = []
        for profile_file in profiles_dir.glob("*.env"):
            profiles.append(profile_file.stem)
        
        return sorted(profiles)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get comprehensive configuration summary."""
        summary = {
            "files": {},
            "env_vars": {},
            "models": {},
            "issues": {},
            "profiles": []
        }
        
        # Check configuration files
        for config_type, filename in self.config_files.items():
            file_path = self.project_root / filename
            summary["files"][config_type] = {
                "exists": file_path.exists(),
                "path": str(file_path),
                "size": file_path.stat().st_size if file_path.exists() else 0
            }
        
        # Load environment variables
        env_vars = self.load_config("env") or {}
        summary["env_vars"] = {
            "count": len(env_vars),
            "has_api_keys": any(key for key in env_vars if "API_KEY" in key),
            "has_proxy_config": all(var in env_vars for var in ["LITELLM_PROXY_HOST", "LITELLM_PROXY_PORT"]),
            "has_ollama_config": "OLLAMA_BASE_URL" in env_vars
        }
        
        # Load models
        models = self.get_model_config()
        summary["models"] = {
            "count": len(models),
            "tiers": list(models.keys()),
            "has_local": any(model.get("provider") == "ollama" for model in models.values())
        }
        
        # Validate configurations
        summary["issues"] = {
            "env": self.validate_env_config(),
            "docker": self.validate_docker_configs()
        }
        
        # List profiles
        summary["profiles"] = self.list_profiles()
        
        return summary
    
    def print_config_summary(self):
        """Print comprehensive configuration summary."""
        summary = self.get_config_summary()
        
        print("⚙️  Configuration Summary")
        print("=========================")
        
        # Configuration files
        print("\n📁 Configuration Files:")
        for config_type, info in summary["files"].items():
            status = "✅" if info["exists"] else "❌"
            size_kb = info["size"] / 1024 if info["size"] > 0 else 0
            print(f"  {status} {config_type}: {info['path']} ({size_kb:.1f}KB)")
        
        # Environment variables
        env_info = summary["env_vars"]
        print(f"\n🔧 Environment Variables:")
        print(f"  📊 Count: {env_info['count']}")
        print(f"  🔑 API Keys: {'✅' if env_info['has_api_keys'] else '❌'}")
        print(f"  🌐 Proxy Config: {'✅' if env_info['has_proxy_config'] else '❌'}")
        print(f"  🦙 Ollama Config: {'✅' if env_info['has_ollama_config'] else '❌'}")
        
        # Models
        model_info = summary["models"]
        print(f"\n🤖 Models:")
        print(f"  📊 Count: {model_info['count']}")
        print(f"  🏷️  Tiers: {', '.join(model_info['tiers'])}")
        print(f"  🏠 Local Models: {'✅' if model_info['has_local'] else '❌'}")
        
        # Issues
        all_issues = 0
        for category, issues in summary["issues"].items():
            for issue_type, issue_list in issues.items():
                if issue_list:
                    all_issues += len(issue_list)
        
        if all_issues > 0:
            print(f"\n⚠️  Issues Found ({all_issues}):")
            for category, issues in summary["issues"].items():
                for issue_type, issue_list in issues.items():
                    if issue_list:
                        print(f"  {category.upper()} {issue_type}:")
                        for issue in issue_list:
                            print(f"    • {issue}")
        else:
            print(f"\n✅ No configuration issues found!")
        
        # Profiles
        profiles = summary["profiles"]
        if profiles:
            print(f"\n📋 Available Profiles: {', '.join(profiles)}")
        
        print()


# CLI interface
def main():
    """CLI interface for config manager."""
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description="llx Config Manager")
    parser.add_argument("command", choices=[
        "load", "save", "create-env", "update-env", "get-env", "validate",
        "list-models", "add-model", "remove-model", "backup", "restore",
        "docker-env", "create-profile", "load-profile", "list-profiles", "summary"
    ])
    parser.add_argument("--type", help="Configuration type")
    parser.add_argument("--key", help="Environment variable key")
    parser.add_argument("--value", help="Environment variable value")
    parser.add_argument("--tier", help="Model tier")
    parser.add_argument("--env", default="dev", help="Docker environment")
    parser.add_argument("--profile", help="Profile name")
    parser.add_argument("--backup-dir", help="Backup directory")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    
    args = parser.parse_args()
    
    manager = ConfigManager()
    
    if args.command == "load":
        if not args.type:
            print("❌ --type required for load")
            success = False
        else:
            config = manager.load_config(args.type)
            if config:
                print(json.dumps(config, indent=2))
                success = True
            else:
                success = False
    
    elif args.command == "save":
        if not args.type:
            print("❌ --type required for save")
            success = False
        else:
            # Read config from stdin
            try:
                config_data = json.loads(sys.stdin.read())
                success = manager.save_config(args.type, config_data)
            except:
                print("❌ Invalid JSON configuration")
                success = False
    
    elif args.command == "create-env":
        success = manager.create_default_env(args.overwrite)
    
    elif args.command == "update-env":
        if not args.key or not args.value:
            print("❌ --key and --value required for update-env")
            success = False
        else:
            success = manager.update_env_var(args.key, args.value)
    
    elif args.command == "get-env":
        if not args.key:
            print("❌ --key required for get-env")
            success = False
        else:
            value = manager.get_env_var(args.key)
            if value is not None:
                print(value)
                success = True
            else:
                print(f"❌ Environment variable {args.key} not found")
                success = False
    
    elif args.command == "validate":
        issues = manager.validate_env_config()
        docker_issues = manager.validate_docker_configs()
        
        all_issues = len(issues["missing"]) + len(issues["invalid"]) + len(issues["warnings"])
        all_issues += len(docker_issues["missing"]) + len(docker_issues["invalid"]) + len(docker_issues["warnings"])
        
        if all_issues > 0:
            print(f"❌ Found {all_issues} configuration issues")
            success = False
        else:
            print("✅ Configuration is valid")
            success = True
    
    elif args.command == "list-models":
        manager.list_models()
        success = True
    
    elif args.command == "add-model":
        if not args.tier:
            print("❌ --tier required for add-model")
            success = False
        else:
            # Read model config from stdin
            try:
                model_config = json.loads(sys.stdin.read())
                success = manager.add_model(args.tier, model_config)
            except:
                print("❌ Invalid model configuration")
                success = False
    
    elif args.command == "remove-model":
        if not args.tier:
            print("❌ --tier required for remove-model")
            success = False
        else:
            success = manager.remove_model(args.tier)
    
    elif args.command == "backup":
        success = manager.backup_configs(args.backup_dir)
    
    elif args.command == "restore":
        if not args.backup_dir:
            print("❌ --backup-dir required for restore")
            success = False
        else:
            success = manager.restore_configs(args.backup_dir)
    
    elif args.command == "docker-env":
        success = manager.generate_docker_env_file(args.env)
    
    elif args.command == "create-profile":
        if not args.profile:
            print("❌ --profile required for create-profile")
            success = False
        else:
            success = manager.create_profile(args.profile)
    
    elif args.command == "load-profile":
        if not args.profile:
            print("❌ --profile required for load-profile")
            success = False
        else:
            success = manager.load_profile(args.profile)
    
    elif args.command == "list-profiles":
        profiles = manager.list_profiles()
        if profiles:
            print("📋 Available Profiles:")
            for profile in profiles:
                print(f"  • {profile}")
        else:
            print("No profiles found")
        success = True
    
    elif args.command == "summary":
        manager.print_config_summary()
        success = True
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
