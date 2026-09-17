"""Mechanical checks on an agent-authored prompt and its answer key (DESIGN.md §4.1).

validate() returns a list of problems; an empty list means the pair is usable.
After authoring, only clerical errors may be corrected by hand, each logged.
"""
import json
import re
import sys
from pathlib import Path

ONCE = ("restated_capability", "duplicate", "emphasis", "vague_contract", "conflict",
        "unguarded_input", "missing_contract")
IDENTIFIER = re.compile(r"""^(?!.*\s)(?:
      [A-Za-z0-9]+_[A-Za-z0-9_]+          # snake_case, ALLCAPS_CODE
    | [a-z0-9]+[A-Z][A-Za-z0-9]*          # camelCase
    | [A-Z][A-Z0-9]{2,}                   # ALLCAPS code
    | [\w.-]+\.[A-Za-z]{2,4}              # file name
    | [\w.-]*/[\w./-]+                    # path
    | \d[\w-]*\d                          # a value with digits, e.g. 2026-04
)$""", re.X)


def item_lines(item):
    if "lines" in item:
        return list(item["lines"])
    if "depends_line" in item:
        return [item["depends_line"]]
    return [item["line"]]


def validate(prompt_text, key):
    errors, lines = [], prompt_text.splitlines()

    def line_ok(n, what):
        if not isinstance(n, int) or not 1 <= n <= len(lines) or not lines[n - 1].strip():
            errors.append(f"{what}: line {n} is out of range or blank")
            return False
        return True

    words = len(prompt_text.split())
    if not 250 <= words <= 600:
        errors.append(f"prompt is {words} words; want 250-600")
    planted = key.get("planted", [])
    cats = [p.get("category") for p in planted]
    for c in ONCE:
        if cats.count(c) != 1:
            errors.append(f"{c}: {cats.count(c)} entries; want exactly 1")
    if not 3 <= cats.count("work_order_unclear") <= 4:
        errors.append(f"work_order_unclear: {cats.count('work_order_unclear')} entries; want 3-4")
    if cats.count("restriction") < 2:
        errors.append(f"restriction: {cats.count('restriction')} entries; want at least 2")

    planted_lines = set()
    for p in planted:
        cat = p.get("category")
        try:
            nums = item_lines(p)
        except KeyError:
            errors.append(f"{cat}: no line number")
            continue
        planted_lines.update(nums)
        valid = [n for n in nums if line_ok(n, cat)]
        if cat == "conflict" and len(nums) != 2:
            errors.append("conflict: needs exactly 2 lines")
        if cat == "duplicate":
            phrase = p.get("phrase", "")
            if len(phrase.split()) < 3 or prompt_text.count(phrase) < 2:
                errors.append(f"duplicate: phrase {phrase!r} must be 3+ words and occur at least twice")
        if cat == "emphasis" and valid:
            for token in p.get("tokens") or ["<no tokens>"]:
                if token not in lines[valid[0] - 1]:
                    errors.append(f"emphasis: token {token!r} is not on line {valid[0]}")
        if cat == "missing_contract" and not p.get("fact"):
            errors.append("missing_contract: no fact given")

    traps = key.get("traps", {})
    gc = traps.get("generic_contract", {})
    if line_ok(gc.get("line"), "generic_contract"):
        tokens = gc.get("tokens") or ["<no tokens>"]
        for token in tokens:
            if token not in lines[gc["line"] - 1]:
                errors.append(f"generic_contract: token {token!r} is not on line {gc['line']}")
        if not any(IDENTIFIER.search(token) for token in tokens):
            errors.append("generic_contract: no token looks like a product-specific identifier "
                           "(snake_case, camelCase, an ALLCAPS code, a path, a file name, or a value "
                           "containing digits)")
        if gc["line"] in planted_lines:
            errors.append("generic_contract: its line is also listed as planted")
    rb = traps.get("reference_block", {})
    start, end = rb.get("start"), rb.get("end")
    if not (isinstance(start, int) and isinstance(end, int) and 1 <= start < end <= len(lines)):
        errors.append(f"reference_block: bad range {start}-{end}")
    elif len(" ".join(lines[start - 1:end]).split()) < 60:
        errors.append("reference_block: fewer than 60 words")
    return errors


if __name__ == "__main__":
    d = Path(sys.argv[1])
    problems = validate((d / "prompt.md").read_text(), json.loads((d / "answer_key.json").read_text()))
    print("\n".join(problems) or "OK")
    raise SystemExit(1 if problems else 0)
