#!/usr/bin/env python3
"""
llx Local Models Example

This example demonstrates:
1. Setting up local LLM models with Ollama
2. Configuring llx to use local models for privacy and cost savings
3. Comparing local vs cloud model performance
4. Managing local model downloads and updates

Local models provide privacy, offline capability, and zero API costs,
making them ideal for sensitive code or development environments.
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path

# Add llx to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llx import analyze_project, select_model, LlxConfig, ProjectMetrics, ModelTier


def check_ollama_installation():
    """Check if Ollama is installed and running"""
    print("🔍 Checking Ollama installation...")
    
    # Check if Ollama command exists
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"   ✓ Ollama installed: {version}")
            return True, version
        else:
            print("   ❌ Ollama not found")
            return False, None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("   ❌ Ollama not installed or not in PATH")
        return False, None


def check_ollama_service():
    """Check if Ollama service is running"""
    print("\n🔍 Checking Ollama service...")
    
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"   ✓ Ollama service running with {len(models)} models")
            
            for model in models[:5]:  # Show first 5 models
                name = model.get('name', 'Unknown')
                size = model.get('size', 0)
                size_gb = size / (1024**3) if size else 0
                print(f"     • {name} ({size_gb:.1f}GB)")
            
            return True, models
        else:
            print(f"   ❌ Ollama service responded with status {response.status_code}")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Cannot connect to Ollama service: {e}")
        return False, None


def list_recommended_local_models():
    """List recommended local models for different use cases"""
    print("\n🎯 Recommended Local Models")
    print("=" * 40)
    
    models = {
        'coding': {
            'qwen2.5-coder': {
                'name': 'qwen2.5-coder:7b',
                'description': 'Specialized for code generation and debugging',
                'size': '4.7GB',
                'context': '32K',
                'strengths': ['Code completion', 'Debugging', 'Code explanation']
            },
            'codellama': {
                'name': 'codellama:7b',
                'description': 'Meta\'s code-specialized model',
                'size': '3.8GB',
                'context': '4K',
                'strengths': ['Code generation', 'Documentation', 'Refactoring']
            },
            'deepseek-coder': {
                'name': 'deepseek-coder:6.7b',
                'description': 'Strong performance on coding benchmarks',
                'size': '3.8GB',
                'context': '4K',
                'strengths': ['Algorithm design', 'Problem solving', 'Code review']
            }
        },
        'general': {
            'llama3.1': {
                'name': 'llama3.1:8b',
                'description': 'General purpose, well-balanced model',
                'size': '4.7GB',
                'context': '128K',
                'strengths': ['General chat', 'Analysis', 'Documentation']
            },
            'mistral': {
                'name': 'mistral:7b',
                'description': 'Fast and efficient general model',
                'size': '4.1GB',
                'context': '32K',
                'strengths': ['Speed', 'Low resource usage', 'General tasks']
            }
        },
        'large': {
            'llama3.1-70b': {
                'name': 'llama3.1:70b',
                'description': 'High-performance large model',
                'size': '40GB',
                'context': '128K',
                'strengths': ['Complex reasoning', 'Architecture', 'Strategic planning']
            }
        }
    }
    
    for category, category_models in models.items():
        print(f"\n🔷 {category.title()} models:")
        for model_key, model_info in category_models.items():
            print(f"   • {model_info['name']}")
            print(f"     {model_info['description']}")
            print(f"     Size: {model_info['size']}, Context: {model_info['context']}")
            print(f"     Strengths: {', '.join(model_info['strengths'])}")


def demonstrate_local_model_selection():
    """Demonstrate model selection with local models"""
    print("\n🎯 Local Model Selection Demo")
    print("=" * 40)
    
    # Create a config that prefers local models
    project_path = Path(__file__).resolve().parent.parent.parent
    config = LlxConfig.load(project_path)
    
    # Check if we have local models available
    ollama_running, models = check_ollama_service()
    
    if not ollama_running:
        print("❌ Ollama service not available for demonstration")
        print("💡 Start Ollama with: ollama serve")
        return
    
    # Analyze the current project
    try:
        metrics = analyze_project(project_path)
        
        print(f"\n📊 Project Analysis:")
        print(f"   Files: {metrics.total_files}")
        print(f"   Lines: {metrics.total_lines:,}")
        print(f"   Complexity: {metrics.complexity_score:.1f}")
        
        # Try to select a model with local preference
        try:
            selection = select_model(metrics, task_hint="explain", config=config, prefer_local=True)
            
            print(f"\n✓ Recommended model: {selection.model_id}")
            print(f"   Provider: {selection.model.provider}")
            print(f"   Tier: {selection.tier.value}")
            
            # Check if this is a local model
            if selection.model.provider == 'ollama':
                print("   🏠 Local model selected - Zero API costs!")
                print("   ✓ Privacy: Code never leaves your machine")
                print("   ✓ Offline: Works without internet connection")
            else:
                print("   ☁️  Cloud model selected")
                print("   💡 Consider using local models for privacy and cost savings")
                
        except Exception as e:
            print(f"   ❌ Model selection failed: {e}")
            
    except Exception as e:
        print(f"❌ Project analysis failed: {e}")


def show_ollama_setup_instructions():
    """Show instructions for setting up Ollama"""
    print("\n🔧 Ollama Setup Instructions")
    print("=" * 40)
    
    print("\n1. Install Ollama:")
    print("   curl -fsSL https://ollama.ai/install.sh | sh")
    print("   # Or visit: https://ollama.ai/download")
    
    print("\n2. Start Ollama service:")
    print("   ollama serve")
    print("   # Runs on http://localhost:11434")
    
    print("\n3. Download recommended models:")
    print("   ollama pull qwen2.5-coder:7b      # For coding tasks")
    print("   ollama pull llama3.1:8b           # General purpose")
    print("   ollama pull mistral:7b            # Fast and efficient")
    
    print("\n4. Test Ollama:")
    print("   ollama list                       # Show downloaded models")
    print("   ollama run qwen2.5-coder:7b      # Interactive chat")
    
    print("\n5. Configure llx for local models:")
    print("   # Add to .env or llx.toml:")
    print("   OLLAMA_BASE_URL=http://localhost:11434")
    print("   # Local models will be automatically detected")


def estimate_resource_requirements():
    """Estimate resource requirements for local models"""
    print("\n💻 Resource Requirements")
    print("=" * 35)
    
    requirements = {
        'qwen2.5-coder:7b': {
            'ram': '8GB',
            'vram': '6GB',
            'disk': '4.7GB',
            'cpu': '4+ cores recommended'
        },
        'llama3.1:8b': {
            'ram': '8GB',
            'vram': '6GB', 
            'disk': '4.7GB',
            'cpu': '4+ cores recommended'
        },
        'mistral:7b': {
            'ram': '8GB',
            'vram': '5GB',
            'disk': '4.1GB',
            'cpu': '4+ cores recommended'
        },
        'llama3.1:70b': {
            'ram': '64GB',
            'vram': '40GB',
            'disk': '40GB',
            'cpu': '16+ cores recommended'
        }
    }
    
    print("\nModel resource requirements:")
    for model, reqs in requirements.items():
        print(f"\n🔷 {model}:")
        print(f"   RAM: {reqs['ram']}")
        print(f"   VRAM: {reqs['vram']}")
        print(f"   Disk: {reqs['disk']}")
        print(f"   CPU: {reqs['cpu']}")
    
    print("\n💡 Performance tips:")
    print("   • Use GPU acceleration when available (CUDA/Metal)")
    print("   • More RAM = better performance, less swapping")
    print("   • SSD storage improves model loading times")
    print("   • Start with smaller models (7B) for testing")


def main():
    """Main local models example execution"""
    print("🚀 llx Local Models Example")
    print("=" * 50)
    
    # 1. Check Ollama installation
    ollama_installed, ollama_version = check_ollama_installation()
    
    if not ollama_installed:
        print("\n❌ Ollama not installed")
        show_ollama_setup_instructions()
        print("\n💡 Install Ollama first, then run this example again")
        return 1
    
    # 2. Check Ollama service
    ollama_running, available_models = check_ollama_service()
    
    # 3. Show recommended models
    list_recommended_local_models()
    
    # 4. Show resource requirements
    estimate_resource_requirements()
    
    # 5. Demonstrate local model selection
    if ollama_running:
        demonstrate_local_model_selection()
    else:
        print("\n⚠️  Ollama service not running")
        print("💡 Start with: ollama serve")
        print("   Then run this example again to see model selection")
    
    # 6. Show configuration
    print("\n⚙️  Local Model Configuration")
    print("=" * 40)
    print("• Set OLLAMA_BASE_URL=http://localhost:11434")
    print("• Local models appear as 'ollama/model-name'")
    print("• Use --local flag to force local model selection")
    print("• Configure model aliases for easier usage")
    
    print("\n✅ Local models example completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
