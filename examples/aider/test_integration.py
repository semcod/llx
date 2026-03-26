#!/usr/bin/env python3
"""
Improved Aider integration test with Docker fallback.
"""

import asyncio
import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()


async def test_aider_integration():
    """Test Aider integration with multiple fallbacks."""
    
    console.print(Panel.fit("🤖 Aider Integration Test", style="bold blue"))
    
    # Test 1: Check if aider is installed locally
    console.print("\n1. Checking local installation...")
    try:
        result = subprocess.run(['aider', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            console.print(f"✅ Aider is installed: {result.stdout.strip()}")
            use_local = True
        else:
            use_local = False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        console.print("❌ Aider not found locally")
        use_local = False
    
    # Test 2: Check Docker
    if not use_local:
        console.print("\n2. Checking Docker...")
        try:
            docker_check = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if docker_check.returncode == 0:
                console.print(f"✅ Docker available: {docker_check.stdout.strip()}")
                use_docker = True
            else:
                use_docker = False
        except FileNotFoundError:
            console.print("❌ Docker not found")
            use_docker = False
    
    # Test 3: Check Ollama
    console.print("\n3. Checking Ollama...")
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            console.print(f"✅ Ollama running with {len(models)} models")
            for model in models[:3]:
                console.print(f"   - {model['name']}")
        else:
            console.print("⚠️  Ollama not responding")
    except:
        console.print("⚠️  Ollama not available")
    
    # Test 4: Try Aider via MCP tool
    console.print("\n4. Testing MCP tool integration...")
    try:
        from llx.mcp.tools import _handle_aider
        
        # Create test file
        test_file = Path("test_aider_integration.py")
        test_file.write_text("""
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
""")
        
        # Test MCP tool
        result = await _handle_aider({
            'prompt': 'Add type hints to this function',
            'path': '.',
            'model': 'ollama/qwen2.5-coder:7b',
            'files': ['test_aider_integration.py']
        })
        
        if result.get('success'):
            console.print("✅ MCP tool executed successfully")
            console.print(f"   Command: {result['command']}")
        else:
            console.print(f"❌ MCP tool failed: {result.get('error', 'Unknown error')}")
        
        # Cleanup
        if test_file.exists():
            test_file.unlink()
            
    except Exception as e:
        console.print(f"❌ MCP tool error: {e}")
    
    # Test 5: Try direct Docker command
    if use_docker:
        console.print("\n5. Testing Docker Aider...")
        try:
            # Pull image if needed
            console.print("   Pulling aider image...")
            pull_result = subprocess.run([
                'docker', 'pull', 'paulgauthier/aider'
            ], capture_output=True, text=True, timeout=60)
            
            if pull_result.returncode == 0:
                console.print("✅ Docker image pulled")
                
                # Create test directory
                test_dir = Path("test_docker_aider")
                test_dir.mkdir(exist_ok=True)
                
                test_file = test_dir / "hello.py"
                test_file.write_text("print('Hello from Docker!')")
                
                # Run aider in Docker
                cmd = [
                    'docker', 'run', '--rm',
                    '-v', f'{test_dir.absolute()}:/workspace',
                    'paulgauthier/aider',
                    '--model', 'ollama_chat/qwen2.5-coder:7b',
                    '--message', 'Add type hints',
                    '/workspace/hello.py'
                ]
                
                console.print(f"   Running: {' '.join(cmd[:5])}...")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    console.print("✅ Docker Aider works!")
                    if test_file.exists():
                        content = test_file.read_text()
                        console.print("   Modified file content:")
                        console.print(content)
                else:
                    console.print("❌ Docker Aider failed")
                    console.print(f"   Error: {result.stderr[:200]}")
                
                # Cleanup
                import shutil
                shutil.rmtree(test_dir)
                
            else:
                console.print("❌ Failed to pull Docker image")
                
        except subprocess.TimeoutExpired:
            console.print("❌ Docker pull timed out")
        except Exception as e:
            console.print(f"❌ Docker error: {e}")
    
    # Summary
    console.print("\n" + "="*50)
    console.print("[bold]Test Summary:[/bold]")
    console.print(f"• Local Aider: {'✅' if use_local else '❌'}")
    console.print(f"• Docker: {'✅' if use_docker else '❌'}")
    console.print(f"• MCP Tool: Available")
    console.print(f"• Ollama: Checked")
    
    console.print("\n[cyan]Recommendations:[/cyan]")
    if not use_local and not use_docker:
        console.print("• Install Aider: pip install aider-chat")
        console.print("• Or use Docker: docker pull paulgauthier/aider")
    elif use_local:
        console.print("• Aider is ready to use locally")
    elif use_docker:
        console.print("• Use Docker for Aider integration")
    
    console.print("\n[yellow]Note:[/yellow] Some features may require Ollama to be running with models pulled")


if __name__ == "__main__":
    asyncio.run(test_aider_integration())
