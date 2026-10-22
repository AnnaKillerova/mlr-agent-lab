"""Send a Blender python script to the running Blender via the MCP server."""

import json
import sys

from mcp_client import MCPClient

path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    code = fh.read()

client = MCPClient()
client.initialize()
client.initialized()
result = client.call(
    "execute_blender_code", {"code": code, "user_prompt": "build low-poly tree"}
)
print("=== RESULT ===")
print(result if result.strip() else "(empty result = script ran without output)")
