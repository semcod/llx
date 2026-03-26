#!/usr/bin/env python3
"""Test aider MCP tool integration with Docker."""

import asyncio
import json
from pathlib import Path

async def test_aider_tool():
    """Test aider MCP tool."""
    from llx.mcp.tools import _handle_aider
    
    print("🧪 Testing aider MCP tool with Docker...")
    
    # Test with Docker
    print("\n1. Testing aider via Docker...")
    result = await _handle_aider({
        "prompt": "Add type hints to this function",
        "path": ".",
        "model": "ollama/qwen2.5-coder:7b",
        "files": ["test_aider.py"]
    })
    
    if result.get("success"):
        print("✅ Aider executed successfully!")
        print(f"   Command: {result['command']}")
        print(f"   Output: {result['stdout'][:300]}...")
    else:
        print("❌ Aider failed")
        print(f"   Error: {result.get('error') or result.get('stderr')}")
        
        # Try Docker command directly
        print("\n2. Trying Docker directly...")
        import subprocess
        try:
            # Create test file
            test_file = Path("test_aider.py")
            test_file.write_text("""
def hello():
    print("Hello World")

if __name__ == "__main__":
    hello()
""")
            
            # Run aider in Docker
            cmd = [
                "docker", "run", "--rm", "-v", f"{Path.cwd()}:/workspace",
                "paul-gauthier/aider", 
                "--model", "ollama_chat/qwen2.5-coder:7b",
                "--message", "Add type hints",
                "/workspace/test_aider.py"
            ]
            
            print(f"   Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Docker aider works!")
                print(f"   Output: {result.stdout[:200]}...")
            else:
                print("❌ Docker aider failed")
                print(f"   Error: {result.stderr[:200]}...")
                
            # Clean up
            if test_file.exists():
                test_file.unlink()
                
        except Exception as e:
            print(f"❌ Docker test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_aider_tool())
