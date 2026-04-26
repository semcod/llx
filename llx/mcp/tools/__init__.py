"""MCP tools for llx.

This package provides MCP tool definitions for the llx project.
Each submodule contains related tools:
    - core: Basic llx tools (analyze, select, chat)
    - analysis: Code analysis tools (code2llm, redup, vallm)
    - preprocessing: Preprocessing tools (preprocess, context)
    - proxym: Proxym integration tools
    - code_edit: Code editing tools (aider)
    - planfile: Planfile strategy tools
    - privacy: Privacy and anonymization tools
    - registry: MCP_TOOLS tuple with all tools
"""

from llx.mcp.tools.base import McpTool
from llx.mcp.tools.core import (
    tool_llx_analyze, tool_llx_select, tool_llx_chat,
    _handle_llx_analyze, _handle_llx_select, _handle_llx_chat,
)
from llx.mcp.tools.analysis import (
    tool_code2llm_analyze, tool_redup_scan, tool_vallm_validate,
    _handle_code2llm_analyze, _handle_redup_scan, _handle_vallm_validate,
)
from llx.mcp.tools.preprocessing import (
    tool_llx_preprocess, tool_llx_context,
    _handle_llx_preprocess, _handle_llx_context,
)
from llx.mcp.tools.proxym import (
    tool_llx_proxy_status, tool_llx_proxym_status, tool_llx_proxym_chat,
    _handle_llx_proxy_status, _handle_llx_proxym_status, _handle_llx_proxym_chat,
)
from llx.mcp.tools.code_edit import tool_aider, _handle_aider
from llx.mcp.tools.planfile import tool_planfile_generate, tool_planfile_apply
from llx.mcp.tools.privacy import (
    tool_llx_privacy_scan, tool_llx_project_anonymize, tool_llx_project_deanonymize,
    _handle_llx_privacy_scan, _handle_llx_project_anonymize, _handle_llx_project_deanonymize,
)
from llx.mcp.tools.registry import MCP_TOOLS

__all__ = [
    # Base
    "McpTool",
    # Core tools
    "tool_llx_analyze",
    "tool_llx_select",
    "tool_llx_chat",
    "_handle_llx_analyze",
    "_handle_llx_select",
    "_handle_llx_chat",
    # Analysis tools
    "tool_code2llm_analyze",
    "tool_redup_scan",
    "tool_vallm_validate",
    "_handle_code2llm_analyze",
    "_handle_redup_scan",
    "_handle_vallm_validate",
    # Preprocessing tools
    "tool_llx_preprocess",
    "tool_llx_context",
    "_handle_llx_preprocess",
    "_handle_llx_context",
    # Proxym tools
    "tool_llx_proxy_status",
    "tool_llx_proxym_status",
    "tool_llx_proxym_chat",
    "_handle_llx_proxy_status",
    "_handle_llx_proxym_status",
    "_handle_llx_proxym_chat",
    # Code editing tools
    "tool_aider",
    "_handle_aider",
    # Planfile tools
    "tool_planfile_generate",
    "tool_planfile_apply",
    # Privacy tools
    "tool_llx_privacy_scan",
    "tool_llx_project_anonymize",
    "tool_llx_project_deanonymize",
    "_handle_llx_privacy_scan",
    "_handle_llx_project_anonymize",
    "_handle_llx_project_deanonymize",
    # Registry
    "MCP_TOOLS",
]
