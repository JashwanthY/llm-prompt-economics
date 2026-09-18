#!/usr/bin/env python3
"""Stands in for `claude` and `codex` in tests. No model is called.

FAKE_FLAVOUR: claude | codex. FAKE_MODE:
  report_then_apply  turn 1 leaves prompt.md alone, a resumed turn edits it
  edit               edits prompt.md on turn 1
  sleep              sleeps past the test timeout
  limited            fails with a usage-limit error
  probe              lists skills, including prompt-contract only if its folder exists
  leak               lists prompt-contract whether or not its folder exists
"""
import json
import os
import sys
import time
from pathlib import Path

mode = os.environ.get("FAKE_MODE", "report_then_apply")
flavour = os.environ.get("FAKE_FLAVOUR", "claude")
resumed = "--resume" in sys.argv or "resume" in sys.argv

if mode == "sleep":
    time.sleep(5)
if mode == "limited":
    if flavour == "claude":
        print(json.dumps({"type": "result", "subtype": "error_during_execution", "is_error": True,
                          "result": "usage limit reached", "session_id": "s-1"}))
    else:
        print(json.dumps({"type": "thread.started", "thread_id": "t-1"}))
        print(json.dumps({"type": "turn.failed", "error": {"message": "usage limit reached"}}))
    sys.exit(1)
if mode == "edit" or (mode == "report_then_apply" and resumed):
    p = Path("prompt.md")
    p.write_text(p.read_text().replace("You are a helpful assistant.\n", ""))

has_skill = Path(".claude/skills/prompt-contract").exists() or Path(".agents/skills/prompt-contract").exists()
if mode == "probe":
    text = "code-review, prompt-contract" if has_skill else "code-review"
elif mode == "leak":
    text = "code-review, prompt-contract"
else:
    text = "applied" if resumed else '## Prompt audit\nReply "apply all".'

if flavour == "claude":
    print(json.dumps({"type": "system", "subtype": "init", "session_id": "s-1", "model": "claude-sonnet-5",
                      "skills": ["prompt-contract"] if has_skill else []}))
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": text, "session_id": "s-1",
                      "usage": {"input_tokens": 100, "output_tokens": 50}, "total_cost_usd": 0.01,
                      "modelUsage": {"claude-sonnet-5": {}}}))
else:
    print(json.dumps({"type": "thread.started", "thread_id": "t-1"}))
    print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": text}}))
    print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 50}}))
