"""Allow: python -m llx.mcp"""
from llx.mcp.server import main
import asyncio
asyncio.run(main())
