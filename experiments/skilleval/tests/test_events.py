from pathlib import Path

import pytest

from events import parse_claude, parse_codex

CLAUDE = [
    '{"type":"system","subtype":"init","session_id":"s-1","model":"claude-sonnet-5","skills":["prompt-contract","code-review"]}',
    '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"prompt.md"}}]}}',
    "not json",
    '{"type":"result","subtype":"success","is_error":false,"result":"## Prompt audit","session_id":"s-1",'
    '"usage":{"input_tokens":10,"cache_read_input_tokens":90,"cache_creation_input_tokens":5,"output_tokens":42},'
    '"total_cost_usd":0.12,"modelUsage":{"claude-sonnet-5":{}}}',
]


def test_claude_session_text_usage_tools_skills():
    r = parse_claude(CLAUDE)
    assert (r.session_id, r.final_text, r.input_tokens, r.output_tokens) == ("s-1", "## Prompt audit", 105, 42)
    assert r.tool_calls == ["Read"]
    assert r.skills == ["prompt-contract", "code-review"]
    assert (r.cost_usd, r.model, r.error) == (0.12, "claude-sonnet-5", None)


def test_claude_error_result_carries_subtype_and_text():
    r = parse_claude(['{"type":"result","subtype":"error_during_execution","is_error":true,"result":"usage limit reached","session_id":"s-2"}'])
    assert r.error == "error_during_execution: usage limit reached"


def test_claude_empty_stream_is_an_error():
    assert parse_claude([]).error == "no events"


CODEX = [
    '{"type":"thread.started","thread_id":"t-9"}',
    '{"type":"turn.started"}',
    '{"type":"item.completed","item":{"type":"command_execution","command":"cat prompt.md"}}',
    '{"type":"item.completed","item":{"type":"agent_message","text":"## Prompt audit"}}',
    '{"type":"turn.completed","usage":{"input_tokens":2000,"cached_input_tokens":1500,"output_tokens":300,"reasoning_output_tokens":120}}',
]


def test_codex_thread_text_usage_tools():
    r = parse_codex(CODEX)
    assert (r.session_id, r.final_text) == ("t-9", "## Prompt audit")
    assert (r.input_tokens, r.output_tokens, r.reasoning_tokens) == (2000, 300, 120)
    assert r.tool_calls == ["command_execution"] and r.error is None


def test_codex_turn_failed_is_an_error():
    r = parse_codex(['{"type":"thread.started","thread_id":"t-1"}',
                     '{"type":"turn.failed","error":{"message":"usage limit reached"}}'])
    assert r.error == "usage limit reached"


def test_codex_empty_stream_is_an_error():
    assert parse_codex(["Reading additional input from stdin..."]).error == "no events"


@pytest.mark.parametrize("name,parse", [("claude_real.jsonl", parse_claude), ("codex_real.jsonl", parse_codex)])
def test_real_event_streams_parse(name, parse):
    lines = (Path(__file__).parent / "fixtures" / name).read_text().splitlines()
    r = parse(lines)
    assert r.error is None and r.session_id and r.final_text and r.output_tokens > 0
