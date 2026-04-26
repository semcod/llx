"""MCP tools registry."""

from llx.mcp.tools.core import tool_llx_analyze, tool_llx_select, tool_llx_chat
from llx.mcp.tools.analysis import tool_code2llm_analyze, tool_redup_scan, tool_vallm_validate
from llx.mcp.tools.preprocessing import tool_llx_preprocess, tool_llx_context
from llx.mcp.tools.proxym import tool_llx_proxy_status, tool_llx_proxym_status, tool_llx_proxym_chat
from llx.mcp.tools.code_edit import tool_aider
from llx.mcp.tools.planfile import tool_planfile_generate, tool_planfile_apply
from llx.mcp.tools.privacy import tool_llx_privacy_scan, tool_llx_project_anonymize, tool_llx_project_deanonymize

MCP_TOOLS = (
    tool_llx_analyze,
    tool_llx_select,
    tool_llx_chat,
    tool_llx_preprocess,
    tool_llx_context,
    tool_llx_proxym_status,
    tool_llx_proxym_chat,
    tool_code2llm_analyze,
    tool_redup_scan,
    tool_vallm_validate,
    tool_llx_proxy_status,
    tool_aider,
    tool_planfile_generate,
    tool_planfile_apply,
    tool_llx_privacy_scan,
    tool_llx_project_anonymize,
    tool_llx_project_deanonymize,
)
