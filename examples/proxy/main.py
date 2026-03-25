#!/usr/bin/env python3
"""
llx Proxy Integration Example

This example demonstrates:
1. Setting up the LiteLLM proxy server
2. Configuring model routing and aliases
3. IDE integration (Roo Code, Cline, etc.)
4. Semantic caching and cost tracking

The proxy provides an OpenAI-compatible API endpoint that IDEs and
tools can use to access multiple LLM providers through a single interface.
"""

import os
import sys
import time
import signal
import requests
from pathlib import Path

# Add llx to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llx.config import Config
from llx.proxy.server import ProxyServer
from llx.proxy.router import ProxyRouter


class ProxyExample:
    def __init__(self):
        self.config = Config.from_env()
        self.server = None
        self.router = None
        
    def setup_server(self):
        """Initialize the proxy server"""
        print("🔧 Setting up proxy server...")
        
        # Create router with model aliases
        self.router = ProxyRouter(self.config)
        
        # Configure model aliases from environment
        aliases = {
            'cheap': os.getenv('LLX_ALIAS_CHEAP', 'openrouter/nvidia/nemotron-3-nano-30b-a3b:free'),
            'balanced': os.getenv('LLX_ALIAS_BALANCED', 'openrouter/mistralai/mistral-7b-instruct-v0.1'),
            'premium': os.getenv('LLX_ALIAS_PREMIUM', 'openrouter/anthropic/claude-3.5-sonnet'),
            'free': os.getenv('LLX_ALIAS_FREE', 'openrouter/nvidia/nemotron-3-nano-30b-a3b:free')
        }
        
        for alias, model in aliases.items():
            self.router.add_alias(alias, model)
            print(f"   ✓ {alias} → {model}")
        
        # Create server
        self.server = ProxyServer(
            config=self.config,
            router=self.router,
            host=os.getenv('AI_PROXY_HOST', '0.0.0.0'),
            port=int(os.getenv('AI_PROXY_PORT', '4000'))
        )
        
        print(f"   ✓ Server will run on http://{os.getenv('AI_PROXY_HOST', '0.0.0.0')}:{os.getenv('AI_PROXY_PORT', '4000')}")
        
    def start_server(self):
        """Start the proxy server"""
        print("\n🚀 Starting proxy server...")
        
        try:
            self.server.start()
            print(f"✓ Proxy server started successfully!")
            print(f"  Endpoint: http://{os.getenv('AI_PROXY_HOST', '0.0.0.0')}:{os.getenv('AI_PROXY_PORT', '4000')}")
            print(f"  API Key: {os.getenv('AI_PROXY_MASTER_KEY', 'sk-proxy-local-dev')}")
            
            return True
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def test_proxy(self):
        """Test the proxy with a simple request"""
        print("\n🧪 Testing proxy functionality...")
        
        # Wait a moment for server to be ready
        time.sleep(2)
        
        # Test endpoint
        base_url = f"http://{os.getenv('AI_PROXY_HOST', '0.0.0.0')}:{os.getenv('AI_PROXY_PORT', '4000')}"
        headers = {
            "Authorization": f"Bearer {os.getenv('AI_PROXY_MASTER_KEY', 'sk-proxy-local-dev')}",
            "Content-Type": "application/json"
        }
        
        # Test models endpoint
        try:
            response = requests.get(f"{base_url}/v1/models", headers=headers, timeout=5)
            if response.status_code == 200:
                models = response.json()
                print(f"   ✓ Available models: {len(models.get('data', []))}")
                for model in models.get('data', [])[:3]:  # Show first 3
                    print(f"     • {model.get('id', 'Unknown')}")
            else:
                print(f"   ❌ Models endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Could not connect to proxy: {e}")
            return False
        
        # Test chat completion
        try:
            chat_data = {
                "model": "cheap",  # Use alias
                "messages": [
                    {"role": "user", "content": "Say 'Hello from llx proxy!'"}
                ],
                "max_tokens": 50
            }
            
            response = requests.post(
                f"{base_url}/v1/chat/completions",
                headers=headers,
                json=chat_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                tokens = result['usage']['total_tokens']
                print(f"   ✓ Chat test successful: '{content}'")
                print(f"   ✓ Tokens used: {tokens}")
            else:
                print(f"   ❌ Chat test failed: {response.status_code}")
                if response.text:
                    print(f"     Response: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"   ❌ Chat test failed: {e}")
        
        return True
    
    def show_ide_integration(self):
        """Show IDE integration instructions"""
        print("\n💻 IDE Integration Instructions")
        print("=" * 40)
        
        base_url = f"http://{os.getenv('AI_PROXY_HOST', '0.0.0.0')}:{os.getenv('AI_PROXY_PORT', '4000')}"
        
        print("\n📝 VS Code Extensions:")
        print(f"  • Roo Code: Set API endpoint to {base_url}")
        print(f"  • Cline: Set OpenAI API Base URL to {base_url}")
        print(f"  • Continue.dev: Set API base URL to {base_url}")
        
        print("\n🖥️  Terminal Tools:")
        print(f"  • Aider: export OPENAI_API_BASE={base_url}")
        print(f"  • Claude Code: export ANTHROPIC_BASE_URL={base_url}")
        
        print("\n🔧 Configuration:")
        print(f"  • API Key: {os.getenv('AI_PROXY_MASTER_KEY', 'sk-proxy-local-dev')}")
        print(f"  • Model aliases: cheap, balanced, premium, free")
        
        print("\n💡 Usage Examples:")
        print(f"  curl -H 'Authorization: Bearer {os.getenv('AI_PROXY_MASTER_KEY', 'sk-proxy-local-dev')}' \\")
        print(f"       -H 'Content-Type: application/json' \\")
        print(f"       -d '{{\"model\":\"cheap\",\"messages\":[{{\"role\":\"user\",\"content\":\"Hello\"}}]}}' \\")
        print(f"       {base_url}/v1/chat/completions")
    
    def cleanup(self):
        """Clean up resources"""
        if self.server:
            print("\n🛑 Stopping proxy server...")
            try:
                self.server.stop()
                print("✓ Server stopped")
            except Exception as e:
                print(f"❌ Error stopping server: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n\n🛑 Received shutdown signal...")
    if 'example' in globals():
        example.cleanup()
    sys.exit(0)


def main():
    """Main proxy example execution"""
    global example
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 llx Proxy Integration Example")
    print("=" * 50)
    
    example = ProxyExample()
    
    try:
        # 1. Setup server
        if not example.setup_server():
            return 1
        
        # 2. Start server
        if not example.start_server():
            return 1
        
        # 3. Test functionality
        if not example.test_proxy():
            return 1
        
        # 4. Show integration info
        example.show_ide_integration()
        
        print("\n✅ Proxy server is running!")
        print("Press Ctrl+C to stop the server")
        
        # Keep server running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    finally:
        example.cleanup()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
