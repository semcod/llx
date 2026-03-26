#!/usr/bin/env python3
"""
AI Tools Integration Example
Demonstrates how to use shell-based AI tools (Aider, Claude Code, Cursor) 
through Docker with llx and local Ollama models.
"""

import os
import sys
import subprocess
import requests
import json
import time

def check_docker_services():
    """Check if Docker services are running"""
    services = {}
    
    # Check llx API
    try:
        response = requests.get('http://localhost:4000/health', timeout=5)
        services['llx_api'] = response.status_code == 200
    except:
        services['llx_api'] = False
    
    # Check Ollama
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        services['ollama'] = response.status_code == 200
    except:
        services['ollama'] = False
    
    # Check AI tools container
    try:
        result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'], 
                              capture_output=True, text=True)
        services['ai_tools'] = 'llx-ai-tools-dev' in result.stdout
    except:
        services['ai_tools'] = False
    
    return services

def get_available_models():
    """Get available models from Ollama"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
    except:
        pass
    return []

def test_ai_tools_container():
    """Test AI tools container functionality"""
    try:
        # Test basic connectivity
        result = subprocess.run(['docker', 'exec', 'llx-ai-tools-dev', 'echo', 'container-working'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return False, "Container not responding"
        
        # Test AI tools status
        result = subprocess.run(['docker', 'exec', 'llx-ai-tools-dev', 'ai-tools-status'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return False, "AI tools status not available"
        
        return True, result.stdout
    except Exception as e:
        return False, str(e)

def _run_ai_tool_demo(
    tool_name,
    separator,
    sample_file,
    sample_content,
    command,
    warning_message,
):
    """Shared helper for the shell-based AI tool demos."""
    print(f"🤖 Demonstrating {tool_name}...")
    print(separator)

    try:
        with open(sample_file, 'w') as f:
            f.write(sample_content)

        print(f"🔧 Running: {' '.join(command)}")
        print(warning_message)
        return True
    except Exception as e:
        print(f"❌ {tool_name} demo failed: {e}")
        return False

def demonstrate_aider():
    """Demonstrate Aider usage"""
    return _run_ai_tool_demo(
        "Aider",
        "========================",
        "/tmp/test_aider.py",
        "# Simple Python function\ndef hello():\n    print(\"Hello\")\n",
        [
            'docker', 'exec', 'llx-ai-tools-dev',
            'aider-llx', '--message', 'Add proper docstring and type hints', '/tmp/test_aider.py'
        ],
        "⚠️  This is a demonstration - actual Aider requires interactive mode",
    )

def demonstrate_claude_code():
    """Demonstrate Claude Code usage"""
    return _run_ai_tool_demo(
        "Claude Code",
        "==============================",
        "/tmp/claude_task.py",
        "# TODO: Implement a simple calculator\ndef calculate(a, b, operation):\n    pass\n",
        [
            'docker', 'exec', 'llx-ai-tools-dev',
            'claude-llx', '--task', 'Complete the calculator function', '/tmp/claude_task.py'
        ],
        "⚠️  This is a demonstration - actual Claude Code requires interactive mode",
    )

def demonstrate_cursor():
    """Demonstrate Cursor usage"""
    return _run_ai_tool_demo(
        "Cursor",
        "========================",
        "/tmp/cursor_example.py",
        "# Write a function that checks if a number is prime\ndef is_prime(n):\n    # TODO: Implement\n    pass\n",
        [
            'docker', 'exec', 'llx-ai-tools-dev',
            'cursor-llx', '--prompt', 'Implement the is_prime function efficiently', '/tmp/cursor_example.py'
        ],
        "⚠️  This is a demonstration - actual Cursor requires interactive mode",
    )

def test_chat_completion():
    """Test chat completion through AI tools"""
    print("\n🧪 Testing Chat Completion...")
    print("==========================")
    
    try:
        # Test chat through AI tools container
        cmd = [
            'docker', 'exec', 'llx-ai-tools-dev',
            'ai-chat', 'qwen2.5-coder:7b', 'Write a simple "hello world" function in Python'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Chat completion successful!")
            print("Response:")
            print(result.stdout)
            return True
        else:
            print(f"❌ Chat completion failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        return False

def show_usage_examples():
    """Show usage examples for AI tools"""
    print("\n📚 AI Tools Usage Examples")
    print("==========================")
    print("")
    
    print("🚀 Quick Start:")
    print("  ./ai-tools-manage.sh start      # Start AI tools environment")
    print("  ./ai-tools-manage.sh shell     # Access AI tools shell")
    print("")
    
    print("🤖 In AI Tools Shell:")
    print("  aider-llx                      # Start Aider with llx API")
    print("  aider-local                    # Start Aider with local Ollama")
    print("  claude-llx                     # Start Claude Code with llx API")
    print("  claude-local                   # Start Claude Code with local Ollama")
    print("  cursor-llx                     # Start Cursor with llx API")
    print("  cursor-local                   # Start Cursor with local Ollama")
    print("")
    
    print("🔧 Utility Commands:")
    print("  ai-status                      # Check AI tools status")
    print("  ai-test                        # Test connectivity")
    print("  ai-chat qwen2.5-coder:7b 'msg' # Quick chat test")
    print("")
    
    print("📁 File Operations:")
    print("  aider-llx file.py              # Edit specific file")
    print("  claude-llx --task 'refactor'   # Refactor current directory")
    print("  cursor-llx --prompt 'optimize' # Optimize code")
    print("")
    
    print("🔗 Integration with Git:")
    print("  git init && aider-llx           # Start Aider in new repo")
    print("  claude-llx --commit            # Auto-commit changes")
    print("  cursor-llx --diff              # Review changes")

def main():
    print("🚀 AI Tools Integration Example")
    print("================================")
    print("This example demonstrates shell-based AI tools integration")
    print("with Docker, llx proxy, and local Ollama models.")
    print("")
    
    # Check services
    print("🔍 Checking services...")
    services = check_docker_services()
    
    for service, status in services.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service.replace('_', ' ').title()}")
    
    # Get available models
    models = get_available_models()
    print(f"\n📦 Available Ollama Models: {len(models)}")
    for model in models[:5]:
        print(f"  • {model}")
    if len(models) > 5:
        print(f"  ... and {len(models) - 5} more")
    
    # Check AI tools container
    print("\n🤖 Checking AI Tools Container...")
    container_ok, container_info = test_ai_tools_container()
    
    if container_ok:
        print("✅ AI Tools container is working!")
        print(container_info[:500] + "..." if len(container_info) > 500 else container_info)
    else:
        print(f"❌ AI Tools container issue: {container_info}")
        print("\n🚀 Start AI Tools:")
        print("  ./ai-tools-manage.sh start")
        return False
    
    # Demonstrate tools
    print("\n🎭 Demonstrating AI Tools...")
    print("==============================")
    
    demonstrations = [
        ("Aider", demonstrate_aider),
        ("Claude Code", demonstrate_claude_code), 
        ("Cursor", demonstrate_cursor),
        ("Chat Completion", test_chat_completion)
    ]
    
    results = {}
    for name, demo_func in demonstrations:
        try:
            results[name] = demo_func()
        except Exception as e:
            print(f"❌ {name} demo error: {e}")
            results[name] = False
    
    # Summary
    print("\n📊 Demo Results Summary")
    print("======================")
    
    for name, success in results.items():
        status_icon = "✅" if success else "❌"
        print(f"  {status_icon} {name}")
    
    # Show usage examples
    show_usage_examples()
    
    # Final recommendations
    print("\n🎯 Recommendations")
    print("==================")
    
    successful = sum(results.values())
    total = len(results)
    
    if successful == total:
        print("🎉 All demonstrations successful!")
        print("\n🚀 Next Steps:")
        print("  1. Start using AI tools: ./ai-tools-manage.sh shell")
        print("  2. Try Aider: aider-llx")
        print("  3. Experiment with different models")
        print("  4. Integrate with your workflow")
    elif successful > 0:
        print(f"⚠️  {successful}/{total} demonstrations successful")
        print("\n🔧 Troubleshooting:")
        print("  1. Check logs: ./ai-tools-manage.sh logs")
        print("  2. Test connectivity: ./ai-tools-manage.sh test")
        print("  3. Restart services: ./ai-tools-manage.sh restart")
    else:
        print("❌ All demonstrations failed")
        print("\n🔧 Troubleshooting:")
        print("  1. Ensure Docker is running")
        print("  2. Start services: ./docker-manage.sh dev")
        print("  3. Start AI tools: ./ai-tools-manage.sh start")
        print("  4. Check status: ./ai-tools-manage.sh status")
    
    print("\n✨ AI Tools integration example completed!")
    return successful > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
