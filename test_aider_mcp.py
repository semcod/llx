#!/usr/bin/env python3
"""Test aider MCP tool integration."""

import asyncio
from pathlib import Path

async def test_aider_tool():
    """Test aider MCP tool."""
    from llx.mcp.tools import _handle_aider
    
    print("🧪 Testing aider MCP tool...")
    
    # Test 1: Check if aider is installed
    print("\n1. Checking if aider is installed...")
    result = await _handle_aider({
        "prompt": "Hello",
        "path": ".",
        "model": "ollama/qwen2.5-coder:7b"
    })
    
    if result.get("success"):
        print("✅ Aider is available!")
        print(f"   Command: {result['command']}")
    else:
        print("❌ Aider not found")
        print(f"   Error: {result.get('error')}")
        print("\n💡 Install aider with: pip install aider-chat")
        return
    
    # Test 2: Create a test file and ask aider to modify it
    print("\n2. Creating test file...")
    test_file = Path("test_aider.py")
    test_file.write_text("""
def hello():
    print("Hello World")

if __name__ == "__main__":
    hello()
""")
    
    print("   Created test_aider.py")
    
    # Test 3: Ask aider to refactor
    print("\n3. Asking aider to add type hints...")
    result = await _handle_aider({
        "prompt": "Add type hints to this function",
        "path": ".",
        "model": "ollama/qwen2.5-coder:7b",
        "files": ["test_aider.py"]
    })
    
    if result.get("success"):
        print("✅ Aider executed successfully!")
        print(f"   Output: {result['stdout'][:200]}...")
    else:
        print("❌ Aider failed")
        print(f"   Error: {result.get('stderr')}")
    
    # Clean up
    if test_file.exists():
        test_file.unlink()
        print("\n🧹 Cleaned up test file")

if __name__ == "__main__":
    asyncio.run(test_aider_tool())
