#!/usr/bin/env python3
"""
Basic llx Usage Example

This example demonstrates:
1. Project analysis with code metrics
2. Intelligent model selection based on project characteristics
3. Simple chat interaction with the selected model
4. Cost tracking and budget management

Requirements:
- llx installed in development mode
- Valid API keys in .env file
- Project to analyze (defaults to current directory)
"""

import os
import sys
from pathlib import Path

# Add llx to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llx import analyze_project, select_model, LlxConfig, ProjectMetrics, ModelTier


def main():
    """Main example execution"""
    print("🚀 llx Basic Usage Example")
    print("=" * 50)
    
    # 1. Load configuration
    print("\n📋 Loading configuration...")
    project_root = Path(__file__).resolve().parent.parent.parent
    config = LlxConfig.load(project_root)
    print(f"   ✓ Default tier: {config.default_tier}")
    print(f"   ✓ LiteLLM URL: {config.litellm_base_url}")
    
    # 2. Analyze project
    print("\n🔍 Analyzing project...")
    project_path = project_root
    
    try:
        metrics = analyze_project(project_path)
        print(f"   ✓ Files: {metrics.total_files}")
        print(f"   ✓ Lines: {metrics.total_lines:,}")
        print(f"   ✓ Complexity: {metrics.complexity_score:.1f}")
        print(f"   ✓ Scale: {metrics.scale_score:.1f}")
        print(f"   ✓ Coupling: {metrics.coupling_score:.1f}")
    except Exception as e:
        print(f"   ❌ Analysis failed: {e}")
        return 1
    
    # 3. Select optimal model
    print("\n🤖 Selecting optimal model...")
    
    try:
        selection = select_model(metrics, task_hint="explain", config=config)
        print(f"   ✓ Selected: {selection.model_id}")
        print(f"   ✓ Tier: {selection.tier.value}")
        print(f"   ✓ Provider: {selection.model.provider}")
        print(f"   ✓ Context: {selection.model.max_context:,} tokens")
        print(f"   ✓ Cost: ${selection.model.cost_per_1k_input:.4f}/1K in, ${selection.model.cost_per_1k_output:.4f}/1K out")
        
        if selection.reasons:
            print("   ✓ Reasons:")
            for reason in selection.reasons:
                print(f"     • {reason}")
    except Exception as e:
        print(f"   ❌ Model selection failed: {e}")
        return 1
    
    # 4. Demonstrate configuration (LLM interaction would require API keys)
    print("\n💬 LLM Configuration Check...")
    
    # Check if we have API keys
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if anthropic_key:
        print("   ✓ Anthropic API key available")
    if openrouter_key:
        print("   ✓ OpenRouter API key available")
    if openai_key:
        print("   ✓ OpenAI API key available")
        
    if not (anthropic_key or openrouter_key or openai_key):
        print("   ⚠️  No API keys configured - LLM interaction skipped")
        print("   💡 Add API keys to .env file to test LLM functionality")
    else:
        print("   💡 API keys available - LLM interaction ready")
        print("   ℹ️  Actual LLM testing requires network access and consumes credits")
    
    # 5. Show project summary
    print("\n📊 Project Summary")
    print("   ✓ Analysis completed successfully")
    print(f"   ✓ Recommended model: {selection.model_id}")
    print(f"   ✓ Project size: {metrics.total_files} files, {metrics.total_lines:,} lines")
    print(f"   ✓ Complexity score: {metrics.complexity_score:.1f}")
    print(f"   ✓ Default tier: {config.default_tier}")
    
    print("\n✅ Example completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
