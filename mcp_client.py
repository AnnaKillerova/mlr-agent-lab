"""Minimal stdio JSON-RPC client for the blender MCP server.

Proves the real MCP path (uvx server -> addon socket -> Blender) works,
and lets us call tools from this session without a restart.
"""

import json
import subprocess
import sys
import os

UVX = os.environ.get("UVX", "uvx")


class MCPClient:
    def __init__(self):
        env = dict(os.environ, UV_SYSTEM_CERTS="1")
        self.p = subprocess.Popen(
            [UVX, "--python", "3.11", "mcp-for-blender"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            env=env,
        )
        self.id = 0

    def _send(self, method, params=None, notify=False):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            self.id += 1
            msg["id"] = self.id
        self.p.stdin.write(json.dumps(msg) + "\n")
        self.p.stdin.flush()
        if notify:
            return None
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("MCP server closed the stream")
            try:
                resp = json.loads(line)
            except json.JSONDecodeError:
                continue
            if resp.get("id") == self.id:
                if "error" in resp:
                    raise RuntimeError(json.dumps(resp["error"]))
                return resp["result"]

    def initialize(self):
        return self._send(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "stdio-probe", "version": "1.0"},
            },
        )

    def initialized(self):
        return self._send("notifications/initialized", notify=True)

    def tools(self):
        return self._send("tools/list")

    def call(self, name, args):
        res = self._send("tools/call", {"name": name, "arguments": args})
        parts = []
        for c in res.get("content", []) or []:
            parts.append(c.get("text", ""))
        return "\n".join(parts)


if __name__ == "__main__":
    c = MCPClient()
    info = c.initialize()
    print("SERVER:", json.dumps(info.get("serverInfo", {})))
    c.initialized()
    names = [t["name"] for t in c.tools()["tools"]]
    print("TOOLCOUNT:", len(names))
    print("TOOLS:", ", ".join(sorted(names)[:18]))
    print("SCENE_INFO:", c.call("get_scene_info", {})[:600])
