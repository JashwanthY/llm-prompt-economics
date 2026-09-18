"""Turn one agent turn's event stream into a single TurnResult.

Claude Code emits `--output-format stream-json`; Codex emits `exec --json`. Both
are read line by line, and lines that are not JSON are skipped, because both
tools also print progress text on their streams.
"""
import json
from dataclasses import dataclass, field


@dataclass
class TurnResult:
    session_id: str | None = None
    final_text: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cost_usd: float | None = None
    model: str | None = None
    tool_calls: list[str] = field(default_factory=list)
    skills: list[str] | None = None
    error: str | None = None


def _events(lines):
    for line in lines:
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(event, dict):
            yield event


def parse_claude(lines):
    r = TurnResult()
    for e in _events(lines):
        kind = e.get("type")
        if kind == "system" and e.get("subtype") == "init":
            r.session_id = e.get("session_id", r.session_id)
            r.model = e.get("model", r.model)
            r.skills = e.get("skills", e.get("slash_commands"))
        elif kind == "assistant":
            for block in e.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    r.tool_calls.append(block.get("name", "?"))
        elif kind == "result":
            r.session_id = e.get("session_id", r.session_id)
            r.final_text = e.get("result") or ""
            u = e.get("usage", {})
            r.input_tokens = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            r.output_tokens = u.get("output_tokens", 0)
            r.cost_usd = e.get("total_cost_usd")
            if e.get("modelUsage"):
                r.model = ",".join(e["modelUsage"])
            if e.get("is_error") or e.get("subtype") not in (None, "success"):
                r.error = (e.get("subtype") or "error") + (f": {e['result']}" if e.get("result") else "")
    if r.session_id is None and r.error is None:
        r.error = "no events"
    return r


def parse_codex(lines):
    r = TurnResult()
    for e in _events(lines):
        kind = e.get("type", "")
        if kind == "thread.started":
            r.session_id = e.get("thread_id") or e.get("session_id") or e.get("id")
        elif kind == "item.completed":
            item = e.get("item", {})
            if item.get("type") == "agent_message":
                r.final_text = item.get("text", "")
            elif item.get("type") in ("command_execution", "file_change", "mcp_tool_call", "web_search"):
                r.tool_calls.append(item["type"])
        elif kind == "turn.completed":
            u = e.get("usage", {})
            r.input_tokens += u.get("input_tokens", 0)
            r.output_tokens += u.get("output_tokens", 0)
            r.reasoning_tokens += u.get("reasoning_output_tokens", 0)
        elif kind in ("turn.failed", "error"):
            err = e.get("error")
            r.error = str((err.get("message") if isinstance(err, dict) else err) or e.get("message") or kind)[:500]
    if r.session_id is None and r.error is None:
        r.error = "no events"
    return r
