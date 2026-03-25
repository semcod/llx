"""
Model Manager for llx
Manages local Ollama models and llx model configurations.
"""

import os
import sys
import subprocess
import json
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import requests
from .docker_manager import DockerManager


class ModelManager:
    """Manages local Ollama models and llx configurations."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.ollama_base_url = "http://localhost:11434"
        self.llx_api_base_url = "http://localhost:4000"
        
        # Recommended models for different use cases
        self.recommended_models = {
            "coding": {
                "qwen2.5-coder:7b": {
                    "size": "6GB",
                    "description": "Code specialist model",
                    "context": 32000,
                    "recommended": True
                },
                "deepseek-coder:1.3b": {
                    "size": "776MB",
                    "description": "Lightweight coding model",
                    "context": 8192,
                    "recommended": False
                }
            },
            "general": {
                "qwen2.5-coder:7b": {
                    "size": "6GB",
                    "description": "General purpose with coding focus",
                    "context": 32000,
                    "recommended": True
                },
                "phi3:3.8b": {
                    "size": "2.2GB",
                    "description": "Fast general model",
                    "context": 4096,
                    "recommended": False
                },
                "llama3.2:3b": {
                    "size": "2.0GB",
                    "description": "Balanced general model",
                    "context": 8192,
                    "recommended": False
                }
            },
            "lightweight": {
                "phi3:3.8b": {
                    "size": "2.2GB",
                    "description": "Fast and efficient",
                    "context": 4096,
                    "recommended": True
                },
                "deepseek-coder:1.3b": {
                    "size": "776MB",
                    "description": "Ultra lightweight",
                    "context": 8192,
                    "recommended": False
                },
                "gemma2:2b": {
                    "size": "1.6GB",
                    "description": "Compact model",
                    "context": 8192,
                    "recommended": False
                }
            }
        }
    
    def check_ollama_running(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_llx_running(self) -> bool:
        """Check if llx API is running."""
        try:
            response = requests.get(f"{self.llx_api_base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_ollama_models(self) -> List[Dict[str, any]]:
        """Get available Ollama models."""
        if not self.check_ollama_running():
            return []
        
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
        except:
            pass
        
        return []
    
    def get_llx_models(self) -> List[Dict[str, any]]:
        """Get available llx models."""
        if not self.check_llx_running():
            return []
        
        try:
            response = requests.get(f"{self.llx_api_base_url}/v1/models", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
        except:
            pass
        
        return []
    
    def pull_model(self, model_name: str, timeout: int = 300) -> bool:
        """Pull Ollama model."""
        if not self.check_ollama_running():
            print("❌ Ollama is not running")
            return False
        
        print(f"📦 Pulling model: {model_name}")
        print("⏳ This may take several minutes...")
        
        try:
            # Start pulling
            process = subprocess.Popen([
                "ollama", "pull", model_name
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            # Monitor progress
            start_time = time.time()
            while process.poll() is None:
                if time.time() - start_time > timeout:
                    process.terminate()
                    print("❌ Pull timeout")
                    return False
                
                # Check if model is already available
                models = self.get_ollama_models()
                if any(model["name"] == model_name for model in models):
                    print(f"✅ Model {model_name} pulled successfully!")
                    return True
                
                time.sleep(2)
            
            # Check final result
            if process.returncode == 0:
                print(f"✅ Model {model_name} pulled successfully!")
                return True
            else:
                print(f"❌ Failed to pull {model_name}")
                return False
                
        except Exception as e:
            print(f"❌ Error pulling model: {e}")
            return False
    
    def remove_model(self, model_name: str) -> bool:
        """Remove Ollama model."""
        if not self.check_ollama_running():
            print("❌ Ollama is not running")
            return False
        
        print(f"🗑️  Removing model: {model_name}")
        
        try:
            result = subprocess.run(
                ["ollama", "rm", model_name],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                print(f"✅ Model {model_name} removed successfully!")
                return True
            else:
                print(f"❌ Failed to remove {model_name}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error removing model: {e}")
            return False
    
    def test_model(self, model_name: str, prompt: str = "Hello! Write a simple Python function.") -> bool:
        """Test model with a simple prompt."""
        if not self.check_ollama_running():
            print("❌ Ollama is not running")
            return False
        
        print(f"🧪 Testing model: {model_name}")
        print(f"📝 Prompt: {prompt}")
        
        try:
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "").strip()
                
                if response_text:
                    print("✅ Model test successful!")
                    print(f"💬 Response: {response_text[:200]}...")
                    return True
                else:
                    print("❌ Empty response from model")
                    return False
            else:
                print(f"❌ Model test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing model: {e}")
            return False
    
    def test_llx_model(self, model_name: str, prompt: str = "Hello! Write a simple Python function.") -> bool:
        """Test model through llx API."""
        if not self.check_llx_running():
            print("❌ llx API is not running")
            return False
        
        print(f"🧪 Testing model through llx: {model_name}")
        print(f"📝 Prompt: {prompt}")
        
        try:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{self.llx_api_base_url}/v1/chat/completions",
                json=payload,
                headers={"Authorization": "Bearer sk-proxy-local-dev"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data["choices"][0]["message"]["content"].strip()
                
                if response_text:
                    print("✅ llx model test successful!")
                    print(f"💬 Response: {response_text[:200]}...")
                    return True
                else:
                    print("❌ Empty response from model")
                    return False
            else:
                print(f"❌ llx model test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing llx model: {e}")
            return False
    
    def get_model_info(self, model_name: str) -> Dict[str, any]:
        """Get detailed information about a model."""
        info = {
            "name": model_name,
            "available_ollama": False,
            "available_llx": False,
            "size": None,
            "modified": None,
            "recommended": False
        }
        
        # Check Ollama
        ollama_models = self.get_ollama_models()
        for model in ollama_models:
            if model["name"] == model_name:
                info["available_ollama"] = True
                info["size"] = model.get("size", 0)
                info["modified"] = model.get("modified_at")
                break
        
        # Check llx
        llx_models = self.get_llx_models()
        for model in llx_models:
            if model["id"] == model_name:
                info["available_llx"] = True
                break
        
        # Check if recommended
        for category, models in self.recommended_models.items():
            if model_name in models:
                info["recommended"] = models[model_name].get("recommended", False)
                break
        
        return info
    
    def list_recommended_models(self, category: str = None) -> Dict[str, Dict]:
        """List recommended models."""
        if category:
            return self.recommended_models.get(category, {})
        return self.recommended_models
    
    def get_system_resources(self) -> Dict[str, any]:
        """Get system resource information."""
        resources = {
            "memory_total": 0,
            "memory_available": 0,
            "disk_space": 0,
            "cpu_cores": 0
        }
        
        try:
            # Memory info
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        resources["memory_total"] = int(line.split()[1]) // 1024  # MB
                    elif line.startswith('MemAvailable:'):
                        resources["memory_available"] = int(line.split()[1]) // 1024  # MB
            
            # Disk space
            stat = os.statvfs(self.project_root)
            resources["disk_space"] = (stat.f_bavail * stat.f_frsize) // (1024**3)  # GB
            
            # CPU cores
            resources["cpu_cores"] = os.cpu_count()
            
        except Exception as e:
            print(f"⚠️  Could not get system resources: {e}")
        
        return resources
    
    def recommend_models(self, available_memory_gb: int = None) -> List[str]:
        """Recommend models based on available resources."""
        if available_memory_gb is None:
            resources = self.get_system_resources()
            available_memory_gb = resources.get("memory_available", 0) // 1024
        
        recommendations = []
        
        for category, models in self.recommended_models.items():
            for model_name, model_info in models.items():
                if model_info.get("recommended", False):
                    # Estimate memory requirement (rough approximation)
                    size_gb = 2  # Base memory for Ollama
                    if "GB" in model_info.get("size", ""):
                        size_gb += float(model_info["size"].replace("GB", ""))
                    
                    if size_gb <= available_memory_gb:
                        recommendations.append((model_name, category, model_info))
        
        # Sort by memory requirement
        recommendations.sort(key=lambda x: float(x[2]["size"].replace("GB", "")))
        
        return [rec[0] for rec in recommendations]
    
    def create_model_profile(self, model_name: str) -> bool:
        """Create a model profile for llx configuration."""
        model_info = self.get_model_info(model_name)
        
        if not model_info["available_ollama"]:
            print(f"❌ Model {model_name} is not available in Ollama")
            return False
        
        profile = {
            "model_name": model_name,
            "provider": "ollama",
            "api_base": self.ollama_base_url,
            "size_gb": model_info.get("size", 0) / (1024**3) if model_info.get("size") else 0,
            "context_window": 4096,  # Default, can be updated
            "temperature": 0.2,
            "max_tokens": 4096,
            "recommended_for": [],
            "test_results": {
                "basic_chat": False,
                "code_generation": False,
                "reasoning": False
            }
        }
        
        # Determine recommended use cases
        for category, models in self.recommended_models.items():
            if model_name in models:
                profile["recommended_for"].append(category)
        
        # Save profile
        profiles_dir = self.project_root / "model_profiles"
        profiles_dir.mkdir(exist_ok=True)
        
        profile_file = profiles_dir / f"{model_name.replace(':', '_')}.json"
        profile_file.write_text(json.dumps(profile, indent=2))
        
        print(f"✅ Model profile created: {profile_file}")
        return True
    
    def load_model_profile(self, model_name: str) -> Optional[Dict]:
        """Load a model profile."""
        profiles_dir = self.project_root / "model_profiles"
        profile_file = profiles_dir / f"{model_name.replace(':', '_')}.json"
        
        if profile_file.exists():
            try:
                return json.loads(profile_file.read_text())
            except:
                pass
        
        return None
    
    def benchmark_model(self, model_name: str, tests: List[str] = None) -> Dict[str, bool]:
        """Benchmark model with various test cases."""
        if tests is None:
            tests = [
                ("basic_chat", "Hello! How are you?"),
                ("code_generation", "Write a Python function that calculates factorial"),
                ("reasoning", "If I have 3 apples and eat 1, how many do I have left?"),
                ("math", "What is 15 * 23?"),
                ("creativity", "Write a short poem about coding")
            ]
        
        print(f"🏃 Benchmarking model: {model_name}")
        print("=" * 50)
        
        results = {}
        
        for test_name, prompt in tests:
            print(f"🧪 Running {test_name} test...")
            
            if self.test_model(model_name, prompt):
                results[test_name] = True
                print(f"  ✅ {test_name}: PASSED")
            else:
                results[test_name] = False
                print(f"  ❌ {test_name}: FAILED")
            
            time.sleep(1)  # Brief pause between tests
        
        # Calculate success rate
        passed = sum(results.values())
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"\n📊 Benchmark Results:")
        print(f"  Passed: {passed}/{total} ({success_rate:.1f}%)")
        print(f"  Failed: {total - passed}/{total}")
        
        # Update profile if exists
        profile = self.load_model_profile(model_name)
        if profile:
            profile["test_results"] = results
            profiles_dir = self.project_root / "model_profiles"
            profile_file = profiles_dir / f"{model_name.replace(':', '_')}.json"
            profile_file.write_text(json.dumps(profile, indent=2))
        
        return results
    
    def cleanup_unused_models(self, keep_recommended: bool = True) -> bool:
        """Remove unused models to free up space."""
        print("🧹 Cleaning up unused models...")
        
        available_models = self.get_ollama_models()
        if keep_recommended:
            recommended = set()
            for models in self.recommended_models.values():
                recommended.update(models.keys())
        
        removed_count = 0
        for model in available_models:
            model_name = model["name"]
            
            if keep_recommended and model_name in recommended:
                print(f"⏭️  Keeping recommended model: {model_name}")
                continue
            
            if self.remove_model(model_name):
                removed_count += 1
        
        print(f"✅ Cleaned up {removed_count} models")
        return True
    
    def estimate_model_requirements(self, model_name: str) -> Dict[str, str]:
        """Estimate resource requirements for a model."""
        requirements = {
            "ram_min": "2GB",
            "ram_recommended": "4GB",
            "disk_space": "Unknown",
            "gpu_recommended": "Not required",
            "performance": "Unknown"
        }
        
        # Get model info
        model_info = self.get_model_info(model_name)
        
        if model_info.get("size"):
            size_gb = model_info["size"] / (1024**3)
            requirements["disk_space"] = f"{size_gb:.1f}GB"
            requirements["ram_min"] = f"{max(2, size_gb + 1):.0f}GB"
            requirements["ram_recommended"] = f"{max(4, size_gb + 2):.0f}GB"
        
        # Performance based on model type
        if "coder" in model_name.lower():
            requirements["performance"] = "Excellent for coding"
            requirements["gpu_recommended"] = "Optional but beneficial"
        elif "phi" in model_name.lower():
            requirements["performance"] = "Fast for general tasks"
            requirements["gpu_recommended"] = "Not required"
        elif "llama" in model_name.lower():
            requirements["performance"] = "Good general purpose"
            requirements["gpu_recommended"] = "Optional"
        
        return requirements
    
    def print_model_summary(self):
        """Print comprehensive model summary."""
        print("🤖 Model Summary")
        print("================")
        
        # Service status
        ollama_running = self.check_ollama_running()
        llx_running = self.check_llx_running()
        
        ollama_icon = "✅" if ollama_running else "❌"
        llx_icon = "✅" if llx_running else "❌"
        
        print(f"{ollama_icon} Ollama: {'Running' if ollama_running else 'Stopped'}")
        print(f"{llx_icon} llx API: {'Running' if llx_running else 'Stopped'}")
        
        if ollama_running:
            # Available models
            ollama_models = self.get_ollama_models()
            print(f"\n📦 Ollama Models: {len(ollama_models)}")
            
            total_size = sum(model.get("size", 0) for model in ollama_models)
            print(f"💾 Total Size: {total_size / (1024**3):.1f}GB")
            
            for model in ollama_models[:10]:  # Show first 10
                size_gb = model.get("size", 0) / (1024**3)
                print(f"  • {model['name']} ({size_gb:.1f}GB)")
            
            if len(ollama_models) > 10:
                print(f"  ... and {len(ollama_models) - 10} more")
        
        if llx_running:
            # llx models
            llx_models = self.get_llx_models()
            print(f"\n🤖 llx Models: {len(llx_models)}")
            
            for model in llx_models[:5]:  # Show first 5
                print(f"  • {model['id']}")
            
            if len(llx_models) > 5:
                print(f"  ... and {len(llx_models) - 5} more")
        
        # System resources
        resources = self.get_system_resources()
        print(f"\n💻 System Resources:")
        print(f"  🧠 Memory: {resources['memory_available'] // 1024}GB available / {resources['memory_total'] // 1024}GB total")
        print(f"  💾 Disk: {resources['disk_space']}GB available")
        print(f"  ⚡ CPU: {resources['cpu_cores']} cores")
        
        # Recommendations
        recommendations = self.recommend_models(resources['memory_available'] // 1024)
        if recommendations:
            print(f"\n🎯 Recommended Models (based on {resources['memory_available'] // 1024}GB RAM):")
            for model in recommendations[:3]:
                model_info = self.get_model_info(model)
                size_gb = model_info.get("size", 0) / (1024**3) if model_info.get("size") else 0
                print(f"  • {model} ({size_gb:.1f}GB)")
        
        print()


# CLI interface
def main():
    """CLI interface for model manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="llx Model Manager")
    parser.add_argument("command", choices=[
        "list", "pull", "remove", "test", "info", "recommend",
        "profile", "benchmark", "cleanup", "summary", "requirements"
    ])
    parser.add_argument("--model", help="Model name")
    parser.add_argument("--prompt", default="Hello! Write a simple Python function.", help="Test prompt")
    parser.add_argument("--category", help="Model category (coding, general, lightweight)")
    parser.add_argument("--memory", type=int, help="Available memory in GB")
    parser.add_argument("--keep-recommended", action="store_true", help="Keep recommended models when cleaning")
    parser.add_argument("--timeout", type=int, default=300, help="Pull timeout in seconds")
    
    args = parser.parse_args()
    
    manager = ModelManager()
    
    if args.command == "list":
        models = manager.get_ollama_models()
        print(f"📦 Available Models ({len(models)}):")
        for model in models:
            size_gb = model.get("size", 0) / (1024**3)
            print(f"  • {model['name']} ({size_gb:.1f}GB)")
        success = True
    
    elif args.command == "pull":
        if not args.model:
            print("❌ --model required for pull")
            success = False
        else:
            success = manager.pull_model(args.model, args.timeout)
    
    elif args.command == "remove":
        if not args.model:
            print("❌ --model required for remove")
            success = False
        else:
            success = manager.remove_model(args.model)
    
    elif args.command == "test":
        if not args.model:
            print("❌ --model required for test")
            success = False
        else:
            success = manager.test_model(args.model, args.prompt)
    
    elif args.command == "info":
        if not args.model:
            print("❌ --model required for info")
            success = False
        else:
            info = manager.get_model_info(args.model)
            print(f"📊 Model Information: {args.model}")
            print(f"  Available in Ollama: {'✅' if info['available_ollama'] else '❌'}")
            print(f"  Available in llx: {'✅' if info['available_llx'] else '❌'}")
            if info.get("size"):
                size_gb = info["size"] / (1024**3)
                print(f"  Size: {size_gb:.1f}GB")
            if info.get("modified"):
                print(f"  Modified: {info['modified']}")
            print(f"  Recommended: {'✅' if info['recommended'] else '❌'}")
            success = True
    
    elif args.command == "recommend":
        recommendations = manager.list_recommended_models(args.category)
        print(f"🎯 Recommended Models ({args.category or 'all'}):")
        for category, models in recommendations.items():
            print(f"\n{category.title()}:")
            for model, info in models.items():
                recommended = " ⭐" if info.get("recommended") else ""
                print(f"  • {model} ({info['size']}){recommended} - {info['description']}")
        success = True
    
    elif args.command == "profile":
        if not args.model:
            print("❌ --model required for profile")
            success = False
        else:
            success = manager.create_model_profile(args.model)
    
    elif args.command == "benchmark":
        if not args.model:
            print("❌ --model required for benchmark")
            success = False
        else:
            results = manager.benchmark_model(args.model)
            success = all(results.values())
    
    elif args.command == "cleanup":
        success = manager.cleanup_unused_models(args.keep_recommended)
    
    elif args.command == "summary":
        manager.print_model_summary()
        success = True
    
    elif args.command == "requirements":
        if not args.model:
            print("❌ --model required for requirements")
            success = False
        else:
            requirements = manager.estimate_model_requirements(args.model)
            print(f"📊 Resource Requirements: {args.model}")
            print(f"  Min RAM: {requirements['ram_min']}")
            print(f"  Recommended RAM: {requirements['ram_recommended']}")
            print(f"  Disk Space: {requirements['disk_space']}")
            print(f"  GPU: {requirements['gpu_recommended']}")
            print(f"  Performance: {requirements['performance']}")
            success = True
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
