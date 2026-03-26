#!/usr/bin/env python3
"""
Example: Using Aider through LLX MCP with Docker
Demonstrates AI pair programming workflow with local Ollama models.
"""

import asyncio
import json
from pathlib import Path
from llx.mcp.tools import _handle_aider


async def main():
    print("🤖 LLX + Aider Integration Demo")
    print("=" * 50)
    
    # Create a sample Python project
    project_dir = Path("demo_project")
    project_dir.mkdir(exist_ok=True)
    
    # Write a simple function without type hints
    py_file = project_dir / "calculator.py"
    py_file.write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return None
    return a / b

def calculate(operation, x, y):
    ops = {
        'add': add,
        'multiply': multiply,
        'divide': divide
    }
    if operation not in ops:
        raise ValueError(f"Unknown operation: {operation}")
    return ops[operation](x, y)
""")
    
    print(f"✅ Created demo project: {project_dir}")
    print("\n📝 Original code:")
    print(py_file.read_text())
    
    # Use Aider to add type hints via Docker
    print("\n🔧 Using Aider to add type hints...")
    print("-" * 50)
    
    # First, try with Docker (since local installation may fail)
    docker_cmd = [
        "docker", "run", "--rm", 
        "-v", f"{project_dir.absolute()}:/workspace",
        "paulgauthier/aider",
        "--model", "ollama_chat/qwen2.5-coder:7b",
        "--message", "Add comprehensive type hints to all functions",
        "/workspace/calculator.py"
    ]
    
    import subprocess
    try:
        print(f"Running: {' '.join(docker_cmd)}")
        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Aider completed successfully!")
            print("\n📝 Updated code:")
            print(py_file.read_text())
        else:
            print("❌ Aider failed via Docker")
            print(f"Error: {result.stderr[:300]}")
            
            # Fall back to MCP tool simulation
            print("\n🔄 Simulating via MCP tool...")
            mcp_result = await _handle_aider({
                'prompt': 'Add comprehensive type hints to all functions',
                'path': str(project_dir),
                'model': 'ollama/qwen2.5-coder:7b',
                'files': ['calculator.py']
            })
            
            if mcp_result.get('success'):
                print("✅ MCP tool executed!")
                print(f"Command: {mcp_result['command']}")
            else:
                print(f"❌ MCP tool error: {mcp_result.get('error')}")
                
    except subprocess.TimeoutExpired:
        print("❌ Aider timed out")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Show how to use with LLX model selection
    print("\n🎯 Using LLX for intelligent model selection:")
    print("-" * 50)
    
    from llx.config import LlxConfig
    from llx.analysis.collector import analyze_project
    from llx.routing.selector import select_with_context_check
    
    config = LlxConfig.load(project_dir)
    metrics = analyze_project(project_dir)
    result = select_with_context_check(metrics, config, prefer_local=True)
    
    print(f"Selected model: {result.model_id}")
    print(f"Tier: {result.tier.value}")
    print(f"Reason: {'; '.join(result.reasons)}")
    
    # Clean up
    import shutil
    shutil.rmtree(project_dir)
    print(f"\n🧹 Cleaned up {project_dir}")


if __name__ == "__main__":
    asyncio.run(main())
