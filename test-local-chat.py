#!/usr/bin/env python3
"""
Test script for local llx chat API
Tests chat functionality with local Ollama models through llx proxy
"""

import requests
import time
import sys
from typing import Any

HTTP_OK = 200

def test_llx_health() -> bool:
    """Test if llx API is running"""
    try:
        response = requests.get("http://localhost:4000/health", timeout=5)
        return response.status_code == HTTP_OK
    except:
        return False

def test_ollama_health() -> bool:
    """Test if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == HTTP_OK
    except:
        return False

def get_available_models() -> list[str]:
    """Get available Ollama models"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
    except:
        pass
    return []

def test_llx_models() -> list[str]:
    """Test models available through llx API"""
    try:
        response = requests.get("http://localhost:4000/v1/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
    except:
        pass
    return []

def test_chat_completion(model="qwen2.5-coder:7b", message="Hello! Can you write a simple Python function?"):
    """Test chat completion through llx API"""
    url = "http://localhost:4000/v1/chat/completions"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": message}
        ],
        "temperature": 0.2,
        "max_tokens": 500
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-proxy-local-dev"
    }
    
    try:
        print(f"🤖 Testing chat with model: {model}")
        print(f"📝 Message: {message}")
        print(f"🔗 API: {url}")
        print("⏳ Sending request...")
        
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        end_time = time.time()
        
        print(f"⚡ Response time: {end_time - start_time:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {})
            
            print(f"✅ Success!")
            print(f"💬 Response: {content[:200]}...")
            if tokens:
                print(f"🔢 Tokens used: {tokens}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def _check_services() -> tuple[bool, bool]:
    """Check llx and Ollama health and print results."""
    print("\n🔍 Checking services...")
    llx_healthy = test_llx_health()
    ollama_healthy = test_ollama_health()
    print(f"🤖 llx API: {'✅ Running' if llx_healthy else '❌ Not running'}")
    print(f"🦙 Ollama: {'✅ Running' if ollama_healthy else '❌ Not running'}")
    return llx_healthy, ollama_healthy


def _print_models() -> tuple[list[str], list[str]]:
    """Fetch and print available models."""
    print("\n📋 Available models:")
    ollama_models = get_available_models()
    llx_models = test_llx_models()

    print(f"🦙 Ollama models ({len(ollama_models)}):")
    for model in ollama_models[:5]:
        print(f"   • {model}")
    if len(ollama_models) > 5:
        print(f"   ... and {len(ollama_models) - 5} more")

    print(f"\n🤖 llx models ({len(llx_models)}):")
    for model in llx_models:
        print(f"   • {model}")
    return ollama_models, llx_models


def _select_test_models(llx_models: list[str]) -> list[str]:
    """Pick up to 2 models to test."""
    test_models: list[str] = []
    local_models = [m for m in llx_models if "ollama" in m.lower() or "local" in m.lower()]
    if local_models:
        test_models.extend(local_models[:2])
    if not test_models and llx_models:
        test_models.extend(llx_models[:2])
    return test_models


def _run_chat_tests(test_models: list[str]) -> int:
    """Run chat-completion tests and return success count."""
    print(f"\n🧪 Testing chat with {len(test_models)} models...")
    success_count = 0
    for i, model in enumerate(test_models, 1):
        print(f"\n--- Test {i}/{len(test_models)} ---")
        if test_chat_completion(model, "Hello! Write a simple 'hello world' function in Python."):
            success_count += 1
        if i < len(test_models):
            print("⏳ Waiting 2 seconds before next test...")
            time.sleep(2)
    return success_count


def _print_summary(success_count: int, total: int, test_models: list[str]) -> bool:
    """Print test summary and return overall success flag."""
    print(f"\n📊 Test Summary:")
    print(f"✅ Successful: {success_count}/{total}")
    print(f"❌ Failed: {total - success_count}/{total}")
    if success_count > 0:
        print(f"\n🎉 Local chat is working! You can:")
        print(f"   • Use VS Code at http://localhost:8080")
        print(f"   • Configure chat to use http://localhost:4000")
        print(f"   • Use model: {test_models[0]}")
        return True
    print(f"\n❌ Chat tests failed. Check llx API logs:")
    print(f"   ./docker-manage.sh logs dev llx-api")
    return False


def main() -> bool:
    print("🚀 llx Local Chat API Test")
    print("=" * 50)

    llx_healthy, ollama_healthy = _check_services()
    if not llx_healthy:
        print("\n❌ llx API is not running. Start it with:")
        print("   ./docker-manage.sh dev")
        return False
    if not ollama_healthy:
        print("\n❌ Ollama is not running. Start it with:")
        print("   ollama serve")
        return False

    _, llx_models = _print_models()
    test_models = _select_test_models(llx_models)
    if not test_models:
        print("\n❌ No models available for testing")
        return False

    success_count = _run_chat_tests(test_models)
    return _print_summary(success_count, len(test_models), test_models)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
