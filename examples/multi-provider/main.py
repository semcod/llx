#!/usr/bin/env python3
"""
llx Multi-Provider Example

This example demonstrates:
1. Using multiple LLM providers with automatic fallback
2. Cost comparison between providers
3. Provider-specific model selection
4. Load balancing and failover strategies

Shows how llx can work with Anthropic, OpenRouter, OpenAI, Gemini, and others
while maintaining cost control and reliability.
"""

import os
import sys
import time
from pathlib import Path

# Add llx to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llx import analyze_project, select_model, LlxConfig, ProjectMetrics, ModelTier


def check_provider_keys():
    """Check which provider API keys are available"""
    providers = {}
    
    if os.getenv('ANTHROPIC_API_KEY'):
        providers['anthropic'] = {
            'name': 'Anthropic Claude',
            'models': ['claude-opus-4-20250514', 'claude-sonnet-4-20250514', 'claude-haiku-4-5-20251001']
        }
    
    if os.getenv('OPENROUTER_API_KEY'):
        providers['openrouter'] = {
            'name': 'OpenRouter (300+ models)',
            'models': ['anthropic/claude-3.5-sonnet', 'openai/gpt-4o', 'meta-llama/llama-3.1-70b-instruct']
        }
    
    if os.getenv('OPENAI_API_KEY'):
        providers['openai'] = {
            'name': 'OpenAI GPT',
            'models': ['gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini']
        }
    
    if os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'):
        providers['gemini'] = {
            'name': 'Google Gemini',
            'models': ['gemini/gemini-2.5-pro', 'gemini/gemini-2.5-flash', 'gemini/gemini-1.5-pro']
        }
    
    if os.getenv('DEEPSEEK_API_KEY'):
        providers['deepseek'] = {
            'name': 'DeepSeek',
            'models': ['deepseek-chat', 'deepseek-reasoning']
        }
    
    return providers


def build_mock_metrics(files: int, lines: int, complexity: float, fan_out: int | None = None) -> ProjectMetrics:
    """Build realistic project metrics for the demo scenarios."""
    metrics = ProjectMetrics()
    metrics.total_files = files
    metrics.total_lines = lines
    metrics.total_functions = max(1, files * 4)
    metrics.avg_cc = complexity
    metrics.max_cc = max(3, int(complexity * 3))
    metrics.critical_count = 1 if complexity >= 6 else 0
    metrics.max_fan_out = fan_out if fan_out is not None else max(1, min(files * 2, 36))
    metrics.languages = ["python"]
    metrics.estimated_context_tokens = max(500, lines * 2)
    metrics.task_scope = "project" if files > 1 else "single_file"
    return metrics


def compare_provider_costs():
    """Compare costs across available providers"""
    print("\n💰 Provider Cost Comparison (per 1K tokens):")
    print("=" * 60)
    
    # Sample cost data (approximate)
    costs = {
        'anthropic': {
            'claude-opus-4-20250514': {'input': 0.0150, 'output': 0.0750},
            'claude-sonnet-4-20250514': {'input': 0.0030, 'output': 0.0150},
            'claude-haiku-4-5-20251001': {'input': 0.0008, 'output': 0.0040}
        },
        'openrouter': {
            'anthropic/claude-3.5-sonnet': {'input': 0.0030, 'output': 0.0150},
            'openai/gpt-4o': {'input': 0.0025, 'output': 0.0100},
            'meta-llama/llama-3.1-70b-instruct': {'input': 0.0005, 'output': 0.0015}
        },
        'openai': {
            'gpt-4-turbo': {'input': 0.0100, 'output': 0.0300},
            'gpt-4o': {'input': 0.0025, 'output': 0.0100},
            'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006}
        },
        'gemini': {
            'gemini/gemini-2.5-pro': {'input': 0.00125, 'output': 0.00375},
            'gemini/gemini-2.5-flash': {'input': 0.000075, 'output': 0.00015},
            'gemini/gemini-1.5-pro': {'input': 0.0025, 'output': 0.0075}
        },
        'deepseek': {
            'deepseek-chat': {'input': 0.00014, 'output': 0.00028},
            'deepseek-reasoning': {'input': 0.00055, 'output': 0.00219}
        }
    }
    
    providers = check_provider_keys()
    
    for provider_id, provider_info in providers.items():
        print(f"\n🔷 {provider_info['name']}:")
        provider_costs = costs.get(provider_id, {})
        
        for model in provider_info['models'][:2]:  # Show first 2 models
            if model in provider_costs:
                cost = provider_costs[model]
                print(f"   • {model}")
                print(f"     Input: ${cost['input']:.4f} | Output: ${cost['output']:.4f}")
    
    # Find cheapest option
    cheapest_input = float('inf')
    cheapest_model = ""
    
    for provider_id, provider_costs in costs.items():
        if provider_id in providers:
            for model, cost in provider_costs.items():
                if cost['input'] < cheapest_input:
                    cheapest_input = cost['input']
                    cheapest_model = f"{providers[provider_id]['name']}: {model}"
    
    if cheapest_model:
        print(f"\n🏆 Cheapest input cost: {cheapest_model} (${cheapest_input:.4f}/1K)")


def demonstrate_fallback_strategy():
    """Demonstrate provider fallback strategy"""
    print("\n🔄 Provider Fallback Strategy")
    print("=" * 40)
    
    providers = check_provider_keys()
    
    if not providers:
        print("❌ No provider API keys configured")
        return
    
    # Define fallback order based on reliability and cost
    fallback_order = []
    
    if 'anthropic' in providers:
        fallback_order.append(('anthropic', 'Primary - High quality, reliable'))
    if 'openrouter' in providers:
        fallback_order.append(('openrouter', 'Secondary - Large model pool, good uptime'))
    if 'openai' in providers:
        fallback_order.append(('openai', 'Tertiary - Reliable, widely used'))
    if 'gemini' in providers:
        fallback_order.append(('gemini', 'Quaternary - Free tier available'))
    if 'deepseek' in providers:
        fallback_order.append(('deepseek', 'Last resort - Cheapest option'))
    
    print("Provider priority (for failover):")
    for i, (provider, description) in enumerate(fallback_order, 1):
        provider_name = providers[provider]['name']
        print(f"  {i}. {provider_name} - {description}")
    
    print("\n💡 Fallback logic:")
    print("  • Try primary provider first")
    print("  • If rate limited or down, try secondary")
    print("  • Continue through list until successful")
    print("  • Track provider performance for future routing")


def simulate_multi_provider_selection():
    """Simulate model selection across different providers"""
    print("\n🎯 Multi-Provider Model Selection")
    print("=" * 45)
    
    # Create different project scenarios
    scenarios = {
        'small_script': {
            'files': 1,
            'lines': 50,
            'complexity': 2.0,
            'description': 'Small utility script'
        },
        'medium_project': {
            'files': 15,
            'lines': 2000,
            'complexity': 15.0,
            'description': 'Medium web application'
        },
        'large_codebase': {
            'files': 100,
            'lines': 20000,
            'complexity': 45.0,
            'description': 'Large enterprise system'
        }
    }
    
    providers = check_provider_keys()
    
    if not providers:
        print("❌ No providers available for demonstration")
        return
    
    project_root = Path(__file__).parent.parent.parent
    config = LlxConfig.load(project_root)
    
    for scenario_name, scenario_data in scenarios.items():
        print(f"\n📋 {scenario_data['description'].title()}:")
        print(f"   Files: {scenario_data['files']}, Lines: {scenario_data['lines']}, CC: {scenario_data['complexity']}")
        
        metrics = build_mock_metrics(
            scenario_data['files'],
            scenario_data['lines'],
            scenario_data['complexity'],
        )
        
        try:
            selection = select_model(metrics, config=config)
            print(f"   ✓ Recommended: {selection.model_id}")
            print(f"   ✓ Provider: {selection.model.provider}")
            print(f"   ✓ Tier: {selection.tier.value}")
            
            if selection.reasons:
                print(f"   ✓ Reason: {selection.reasons[0]}")
                
        except Exception as e:
            print(f"   ❌ Selection failed: {e}")


def main():
    """Main multi-provider example execution"""
    print("🚀 llx Multi-Provider Example")
    print("=" * 50)
    
    # 1. Check available providers
    print("\n🔑 Checking available providers...")
    providers = check_provider_keys()
    
    if not providers:
        print("❌ No API keys found. Please configure at least one provider:")
        print("   ANTHROPIC_API_KEY=sk-ant-api03-...")
        print("   OPENROUTER_API_KEY=sk-or-v1-...")
        print("   OPENAI_API_KEY=sk-...")
        print("   GEMINI_API_KEY=...")
        return 1
    
    print(f"✓ Found {len(providers)} configured providers:")
    for provider_id, info in providers.items():
        print(f"   • {info['name']}")
    
    # 2. Compare costs
    compare_provider_costs()
    
    # 3. Show fallback strategy
    demonstrate_fallback_strategy()
    
    # 4. Simulate multi-provider selection
    simulate_multi_provider_selection()
    
    # 5. Show configuration tips
    print("\n⚙️  Configuration Tips")
    print("=" * 30)
    print("• Use multiple providers for reliability")
    print("• Set budget limits per provider")
    print("• Configure model aliases for consistency")
    print("• Monitor provider performance and costs")
    print("• Use provider-specific models for different tasks")
    
    print("\n✅ Multi-provider example completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
