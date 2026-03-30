"""Allow: python -m llx.mcp"""

import sys

from llx.mcp.server import main_sync


raise SystemExit(main_sync(sys.argv[1:]))
