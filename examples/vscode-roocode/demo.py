#!/usr/bin/env python3
"""
VS Code + RooCode Demo
This file demonstrates RooCode capabilities with llx and local models.
"""

import os
import sys
import requests
import json
from typing import List, Dict, Optional

class RooCodeDemo:
    """Demo class for RooCode AI assistant capabilities."""
    
    def __init__(self, api_base: str | None = None):
        base_url = api_base or os.getenv("LLX_LITELLM_URL", "http://localhost:4000")
        self.api_base = f"{base_url.rstrip('/')}/v1"
        self.api_key = os.getenv("LLX_PROXY_MASTER_KEY", "sk-proxy-local-dev")
        self.model = os.getenv("LLX_ROOCODE_MODEL", "balanced")
    
    def check_services(self) -> Dict[str, bool]:
        """Check if required services are running."""
        services = {}
        
        # Check llx API
        try:
            response = requests.get(f"{self.api_base}/models", timeout=5)
            services["llx_api"] = response.status_code == 200
        except:
            services["llx_api"] = False
        
        # Check Ollama
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            services["ollama"] = response.status_code == 200
        except:
            services["ollama"] = False
        
        return services
    
    def get_available_models(self) -> List[str]:
        """Get available models from llx API."""
        try:
            response = requests.get(f"{self.api_base}/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["id"] for model in data.get("data", [])]
        except:
            pass
        return []
    
    def test_chat_completion(self, prompt: str) -> Optional[str]:
        """Test chat completion with RooCode model."""
        url = f"{self.api_base}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 500
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error: {e}")
        
        return None
    
    def demonstrate_code_generation(self):
        """Demonstrate RooCode code generation capabilities."""
        print("🤖 RooCode Code Generation Demo")
        print("================================")
        
        prompts = [
            "Write a Python function that validates email addresses",
            "Create a class for managing a todo list with methods",
            "Generate a decorator for timing function execution",
            "Write a function to read and parse JSON files safely"
        ]
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n📝 Prompt {i}: {prompt}")
            print("🔧 Generating code...")
            
            response = self.test_chat_completion(prompt)
            if response:
                print("✅ Generated code:")
                print(response)
            else:
                print("❌ Failed to generate code")
    
    def demonstrate_code_explanation(self):
        """Demonstrate RooCode code explanation capabilities."""
        print("\n🤖 RooCode Code Explanation Demo")
        print("==================================")
        
        code_samples = [
            """
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
            """,
            """
class ContextManager:
    def __init__(self, resource):
        self.resource = resource
    
    def __enter__(self):
        self.resource.open()
        return self.resource
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.resource.close()
        return False
            """
        ]
        
        for i, code in enumerate(code_samples, 1):
            print(f"\n📝 Code Sample {i}:")
            print(code.strip())
            print("\n🔍 Explaining code...")
            
            prompt = f"Explain this code in detail:\n\n{code}"
            response = self.test_chat_completion(prompt)
            if response:
                print("✅ Explanation:")
                print(response)
            else:
                print("❌ Failed to explain code")
    
    def demonstrate_refactoring(self):
        """Demonstrate RooCode refactoring capabilities."""
        print("\n🤖 RooCode Refactoring Demo")
        print("=============================")
        
        original_code = """
def get_user_data(user_id):
    data = {}
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        data['id'] = row[0]
        data['name'] = row[1]
        data['email'] = row[2]
        data['created_at'] = row[3]
    conn.close()
    return data
        """
        
        print("📝 Original Code:")
        print(original_code.strip())
        print("\n🔧 Refactoring code...")
        
        prompt = f"""Refactor this code to:
1. Use proper error handling
2. Add type hints
3. Use context managers
4. Follow PEP 8 guidelines
5. Add docstring

Original code:
{original_code}"""
        
        response = self.test_chat_completion(prompt)
        if response:
            print("✅ Refactored Code:")
            print(response)
        else:
            print("❌ Failed to refactor code")
    
    def demonstrate_test_generation(self):
        """Demonstrate RooCode test generation capabilities."""
        print("\n🤖 RooCode Test Generation Demo")
        print("=================================")
        
        function_to_test = """
def calculate_discount(price: float, discount_percent: float, 
                      min_price: float = 0.0) -> float:
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount percent must be between 0 and 100")
    if price < 0:
        raise ValueError("Price cannot be negative")
    
    discount_amount = price * (discount_percent / 100)
    final_price = price - discount_amount
    
    if final_price < min_price:
        final_price = min_price
    
    return final_price
        """
        
        print("📝 Function to Test:")
        print(function_to_test.strip())
        print("\n🧪 Generating tests...")
        
        prompt = f"""Generate comprehensive unit tests for this function using pytest.
Include tests for:
1. Normal cases
2. Edge cases
3. Error conditions
4. Boundary values

Function:
{function_to_test}"""
        
        response = self.test_chat_completion(prompt)
        if response:
            print("✅ Generated Tests:")
            print(response)
        else:
            print("❌ Failed to generate tests")
    
    def demonstrate_documentation(self):
        """Demonstrate RooCode documentation generation."""
        print("\n🤖 RooCode Documentation Demo")
        print("==============================")
        
        code_to_document = """
import hashlib
import json
from typing import Any, Dict, Optional

class CacheManager:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._access_order: List[str] = []
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._access_order.remove(key)
        elif len(self._cache) >= self.max_size:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]
        
        self._cache[key] = value
        self._access_order.append(key)
    
    def clear(self) -> None:
        self._cache.clear()
        self._access_order.clear()
    
    def get_stats(self) -> Dict[str, int]:
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'utilization': len(self._cache) / self.max_size * 100
        }
        """
        
        print("📝 Code to Document:")
        print(code_to_document.strip())
        print("\n📚 Generating documentation...")
        
        prompt = f"""Generate comprehensive documentation for this class including:
1. Class-level docstring with purpose and usage
2. Method docstrings with parameters, returns, and examples
3. Type hints and error conditions
4. Usage examples

Code:
{code_to_document}"""
        
        response = self.test_chat_completion(prompt)
        if response:
            print("✅ Generated Documentation:")
            print(response)
        else:
            print("❌ Failed to generate documentation")
    
    def run_demo(self):
        """Run complete RooCode demonstration."""
        print("🚀 RooCode + llx Integration Demo")
        print("=================================")
        print("This demo shows RooCode capabilities with local models")
        print("")
        
        # Check services
        services = self.check_services()
        print("🔍 Service Status:")
        for service, status in services.items():
            icon = "✅" if status else "❌"
            print(f"  {icon} {service.replace('_', ' ').title()}")
        
        if not all(services.values()):
            print("\n❌ Some services are not running. Please start:")
            print("  ./docker-manage.sh dev")
            return False
        
        # Get available models
        models = self.get_available_models()
        print(f"\n📦 Available Models: {len(models)}")
        for model in models[:5]:
            print(f"  • {model}")
        if len(models) > 5:
            print(f"  ... and {len(models) - 5} more")
        
        # Run demonstrations
        demonstrations = [
            ("Code Generation", self.demonstrate_code_generation),
            ("Code Explanation", self.demonstrate_code_explanation),
            ("Refactoring", self.demonstrate_refactoring),
            ("Test Generation", self.demonstrate_test_generation),
            ("Documentation", self.demonstrate_documentation)
        ]
        
        print("\n🎭 Running Demonstrations")
        print("========================")
        
        for name, demo_func in demonstrations:
            try:
                demo_func()
            except Exception as e:
                print(f"❌ {name} demo failed: {e}")
        
        print("\n🎉 RooCode Demo Complete!")
        print("========================")
        print("")
        print("📋 What was demonstrated:")
        print("  • Code generation with local models")
        print("  • Code explanation and analysis")
        print("  • Automated refactoring")
        print("  • Test generation")
        print("  • Documentation generation")
        print("")
        print("🚀 Try it yourself in VS Code:")
        print("  1. xdg-open http://localhost:8080")
        print("  2. Use Ctrl+Shift+R for RooCode chat")
        print("  3. Use Ctrl+Shift+G for code generation")
        print("  4. Use Ctrl+Shift+E for code explanation")
        print("")
        print("✨ Enjoy coding with RooCode and local AI!")
        
        return True

def main():
    """Main demonstration function."""
    demo = RooCodeDemo()
    success = demo.run_demo()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
