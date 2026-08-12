"""Stub tool executors (no real side effects)."""

from __future__ import annotations

from typing import Any


def execute_tool(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if tool == "search":
        q = arguments.get("query", "")
        return {"hits": [{"title": f"Stub result for: {q}", "score": 0.91}]}
    if tool == "db_read":
        return {"rows": [{"id": 1, "status": "ok"}, {"id": 2, "status": "pending"}]}
    if tool == "db_write":
        return {"updated": 1}
    if tool == "file_read":
        return {"content": "stub file content"}
    if tool == "file_write":
        return {"written": True, "path": arguments.get("path")}
    if tool == "email":
        return {"queued": True, "to": arguments.get("to")}
    if tool == "external_api":
        return {"status": 200, "body": "stub"}
    return {"ok": True, "tool": tool, "arguments": arguments}
