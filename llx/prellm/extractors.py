"""Extractors and formatters for preLLM - extracted from core.py to reduce CC.

This module contains state extractors and context formatters that were
previously in core.py.
"""

from __future__ import annotations

import json
from typing import Any

from llx.prellm.models import (
    ClassificationResult,
    DecompositionResult,
    DecompositionStrategy,
    StructureResult,
)


def extract_classification_from_state(state: dict) -> ClassificationResult | None:
    """Extract classification result from pipeline state."""
    classification = state.get("classification")
    if isinstance(classification, dict):
        return ClassificationResult(
            intent=classification.get("intent", "unknown"),
            confidence=float(classification.get("confidence", 0.0)),
            domain=classification.get("domain", "general"),
        )
    return None


def extract_structure_from_state(state: dict) -> StructureResult | None:
    """Extract structure result from pipeline state."""
    fields = state.get("fields")
    if isinstance(fields, dict):
        return StructureResult(
            action=fields.get("action", ""),
            target=fields.get("target", ""),
            parameters=fields.get("parameters", {}),
        )
    return None


def extract_sub_queries_from_state(state: dict) -> list[str]:
    """Extract sub-queries from pipeline state."""
    sub_queries = state.get("sub_queries")
    
    if isinstance(sub_queries, dict) and "sub_queries" in sub_queries:
        return [str(q) for q in sub_queries["sub_queries"]]
    elif isinstance(sub_queries, list):
        return [str(q) for q in sub_queries]
    
    return []


def extract_missing_fields_from_state(state: dict) -> list[str]:
    """Extract missing fields from pipeline state."""
    missing_fields = state.get("missing_fields")
    if isinstance(missing_fields, list):
        return missing_fields
    return []


def extract_matched_rule_from_state(state: dict, current_missing_fields: list[str]) -> tuple[str | None, list[str]]:
    """Extract matched rule and missing fields from pipeline state."""
    matched_rule = state.get("matched_rule")
    
    if isinstance(matched_rule, dict) and "name" in matched_rule:
        rule_name = matched_rule["name"]
        
        # Also extract missing fields from rule matching if not already present
        if not current_missing_fields and matched_rule.get("required_fields"):
            missing_fields = matched_rule["required_fields"]
        else:
            missing_fields = current_missing_fields
        
        return rule_name, missing_fields
    
    return None, current_missing_fields


def build_decomposition_result(
    query: str,
    pipeline_name: str,
    prep_result: Any,
) -> DecompositionResult | None:
    """Build a backward-compatible DecompositionResult from pipeline state."""
    if not prep_result.decomposition:
        return None

    state = prep_result.decomposition.state
    strategy_values = [s.value for s in DecompositionStrategy]
    strategy = DecompositionStrategy(pipeline_name) if pipeline_name in strategy_values else DecompositionStrategy.CLASSIFY

    result = DecompositionResult(
        strategy=strategy,
        original_query=query,
        composed_prompt=prep_result.executor_input,
    )

    # Extract all components from state
    result.classification = extract_classification_from_state(state)
    result.structure = extract_structure_from_state(state)
    result.sub_queries = extract_sub_queries_from_state(state)
    result.missing_fields = extract_missing_fields_from_state(state)
    
    # Extract matched rule and update missing fields
    matched_rule, missing_fields = extract_matched_rule_from_state(state, result.missing_fields)
    result.matched_rule = matched_rule
    result.missing_fields = missing_fields

    return result


def format_classification_context(prep_result: Any) -> list[str]:
    """Extract and format classification context from preprocessing result."""
    parts: list[str] = []
    
    if not prep_result.decomposition:
        return parts
    
    state = prep_result.decomposition.state
    classification = state.get("classification")
    
    if isinstance(classification, dict):
        intent = classification.get("intent", "unknown")
        confidence = classification.get("confidence", 0)
        domain = classification.get("domain", "general")
        parts.append(
            f"User intent: {intent} (confidence: {confidence}, domain: {domain})"
        )
    
    matched_rule = state.get("matched_rule")
    if isinstance(matched_rule, dict) and matched_rule.get("name"):
        parts.append(f"Matched domain rule: {matched_rule['name']}")
        if matched_rule.get("required_fields"):
            parts.append(f"Required fields: {', '.join(matched_rule['required_fields'])}")
    
    return parts


def format_context_schema(extra_context: dict[str, Any]) -> list[str]:
    """Extract and format context schema information."""
    parts: list[str] = []
    
    ctx_schema = extra_context.get("context_schema")
    if not ctx_schema:
        return parts
    
    try:
        schema_data = json.loads(ctx_schema) if isinstance(ctx_schema, str) else ctx_schema
        
        tools = schema_data.get("available_tools", [])
        if tools:
            parts.append(f"Available tools on user's system: {', '.join(tools[:15])}")
        
        platform = schema_data.get("platform")
        if platform:
            parts.append(f"Platform: {platform}")
        
        locale = schema_data.get("locale")
        if locale:
            parts.append(f"Locale: {locale}")
    except Exception:
        pass
    
    return parts


def format_runtime_context(extra_context: dict[str, Any]) -> list[str]:
    """Extract and format runtime context information."""
    parts: list[str] = []
    
    runtime = extra_context.get("runtime_context")
    if not isinstance(runtime, dict):
        return parts
    
    sys_info = runtime.get("system", {})
    proc_info = runtime.get("process", {})
    
    if sys_info.get("os"):
        parts.append(f"OS: {sys_info['os']} {sys_info.get('arch', '')}")
    
    if sys_info.get("python"):
        parts.append(f"Python: {sys_info['python']}")
    
    if proc_info.get("cwd"):
        parts.append(f"Working directory: {proc_info['cwd']}")
    
    return parts


def format_user_context(extra_context: dict[str, Any]) -> list[str]:
    """Extract and format user context information."""
    parts: list[str] = []
    
    user_ctx = extra_context.get("user_context")
    if user_ctx:
        parts.append(f"User context: {user_ctx}")
    
    return parts


def build_executor_system_prompt(
    prep_result: Any,
    extra_context: dict[str, Any],
) -> str:
    """Build a system prompt for the large LLM from preprocessing results and context.

    Injects classification, context schema, and runtime info so the large LLM
    understands the user's intent and environment.
    """
    # Collect all context sections
    sections = [
        format_classification_context(prep_result),
        format_context_schema(extra_context),
        format_runtime_context(extra_context),
        format_user_context(extra_context),
    ]
    
    # Flatten all parts
    parts: list[str] = []
    for section in sections:
        parts.extend(section)
    
    if not parts:
        return ""
    
    return "Context from preprocessing:\n" + "\n".join(f"- {p}" for p in parts)
