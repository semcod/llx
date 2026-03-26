#!/usr/bin/env python3
"""
llx Proxy Integration Example

This example demonstrates:
1. Generating a LiteLLM proxy config from the current llx project settings
2. Starting the proxy with the same auth key defined in llx.yaml
3. Verifying the OpenAI-compatible API endpoints
4. Showing IDE integration for Roo Code, Cline, Aider, and Claude Code

The proxy exposes an OpenAI-compatible API endpoint that IDEs and tools can
use to access multiple LLM providers through a single interface.
"""

import os
import signal
import sys
import time
import requests
from pathlib import Path

# Add llx to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llx.config import LlxConfig
from llx.integrations.proxy import check_proxy, start_proxy


class ProxyExample:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.config = LlxConfig.load(self.project_root)
        self.server = None
        self.base_url = f"http://localhost:{self.config.proxy.port}"
        self.headers = {
            "Authorization": f"Bearer {self.config.proxy.master_key}",
            "Content-Type": "application/json",
        }
        
    def setup_server(self):
        """Initialize the proxy config and show the current model tiers."""
        print("🔧 Loading llx proxy configuration...")

        print(f"   ✓ Project root: {self.project_root}")
        print(f"   ✓ Proxy endpoint: {self.base_url}")
        print(f"   ✓ Master key: {self.config.proxy.master_key}")
        print(f"   ✓ Default tier: {self.config.default_tier}")

        model_tiers = ", ".join(sorted(self.config.models.keys()))
        print(f"   ✓ Model tiers: {model_tiers}")

        return True
        
    def start_server(self):
        """Start the proxy server."""
        print("\n🚀 Starting proxy server...")
        
        try:
            self.server = start_proxy(self.config, background=True)
            print("✓ Proxy server started successfully!")
            print(f"  Endpoint: {self.base_url}")
            print(f"  API Key: {self.config.proxy.master_key}")
            
            return True
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False

    def wait_for_proxy(self, timeout: int = 15):
        """Wait until the proxy health endpoint responds."""
        print("\n⏳ Waiting for proxy health check...")

        deadline = time.time() + timeout
        while time.time() < deadline:
            if check_proxy(self.base_url):
                print("   ✓ Proxy health check passed")
                return True
            time.sleep(1)

        print(f"   ❌ Proxy did not become ready within {timeout}s")
        return False
    
    def test_proxy(self):
        """Test the proxy with simple OpenAI-compatible requests."""
        print("\n🧪 Testing proxy functionality...")

        try:
            response = requests.get(f"{self.base_url}/v1/models", headers=self.headers, timeout=10)
            response.raise_for_status()
            models = response.json().get("data", [])
            print(f"   ✓ Available models: {len(models)}")
            for model in models[:5]:
                print(f"     • {model.get('id', 'Unknown')}")
        except Exception as e:
            print(f"   ❌ Could not connect to proxy: {e}")
            return False
        
        preferred_model = "balanced"
        if models and not any(model.get("id") == preferred_model for model in models):
            preferred_model = models[0].get("id", preferred_model)

        try:
            chat_data = {
                "model": preferred_model,
                "messages": [
                    {"role": "user", "content": "Say 'Hello from llx proxy!'"}
                ],
                "max_tokens": 50
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=chat_data,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            tokens = result.get('usage', {}).get('total_tokens', 0)
            print(f"   ✓ Chat test successful: '{content}'")
            print(f"   ✓ Tokens used: {tokens}")
        except Exception as e:
            print(f"   ❌ Chat test failed: {e}")

        return True
    
    def show_ide_integration(self):
        """Show IDE integration instructions."""
        print("\n💻 IDE Integration Instructions")
        print("=" * 40)
        
        base_url = self.base_url
        
        print("\n📝 VS Code Extensions:")
        print(f"  • Roo Code: Set API endpoint to {base_url}")
        print(f"  • Cline: Set OpenAI API Base URL to {base_url}")
        print(f"  • Continue.dev: Set API base URL to {base_url}")
        
        print("\n🖥️  Terminal Tools:")
        print(f"  • Aider: export OPENAI_API_BASE={base_url}")
        print(f"  • Claude Code: export ANTHROPIC_BASE_URL={base_url}")
        
        print("\n🔧 Configuration:")
        print(f"  • API Key: {self.config.proxy.master_key}")
        print(f"  • Model aliases: {', '.join(sorted(self.config.models.keys()))}")
        print(f"  • CLI: llx proxy start --port {self.config.proxy.port}")
        print("  • Status: llx proxy status")
        
        print("\n💡 Usage Examples:")
        print(f"  curl -H 'Authorization: Bearer {self.config.proxy.master_key}' \\")
        print(f"       -H 'Content-Type: application/json' \\")
        print(f"       -d '{{\"model\":\"balanced\",\"messages\":[{{\"role\":\"user\",\"content\":\"Hello\"}}]}}' \\")
        print(f"       {base_url}/v1/chat/completions")
    
    def cleanup(self):
        """Clean up resources."""
        if self.server:
            print("\n🛑 Stopping proxy server...")
            try:
                self.server.terminate()
                self.server.wait(timeout=10)
                print("✓ Server stopped")
            except Exception as e:
                print(f"❌ Error stopping server: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print("\n\n🛑 Received shutdown signal...")
    if 'example' in globals():
        example.cleanup()
    sys.exit(0)


def main():
    """Main proxy example execution."""
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

        # 3. Wait for the health check
        if not example.wait_for_proxy():
            return 1
        
        # 4. Test functionality
        if not example.test_proxy():
            return 1
        
        # 5. Show integration info
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
