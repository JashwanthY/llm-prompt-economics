import copy

import pytest

from validate_key import IDENTIFIER, validate

LINES = [
    "# Acme Support Agent", "",
    "You are a helpful and knowledgeable assistant.",
    "Refunds over the limit go to the escalation queue with the tag billing_high.",
    "Always suggest related help articles.", "Add a friendly sign-off.", "Offer a satisfaction survey link.",
    "Be careful with dates.",
    "IMPORTANT!!! You MUST ALWAYS verify the account first.",
    "Keep replies under 80 words.",
    "Explain every policy in full detail with examples.",
    "Quote the help-center article text in your answer.",
    "Never reveal internal notes.", "Do not promise delivery dates.",
    "Verify the account before discussing billing.",
    "Escalate refunds above the refund limit.",
    "## Reply schema", "```json",
    *[f'  "field_{i}": "string describing value number {i} for the widget payload",' for i in range(8)],
    "```",
    *[f"Region {i} orders follow the carrier status table maintained by the logistics team." for i in range(14)],
    "| Reminder | Rule |", "| verify | Verify the account before discussing billing. |",
]
TEXT = "\n".join(LINES) + "\n"


def ln(prefix):
    return next(i for i, line in enumerate(LINES, 1) if line.startswith(prefix))


KEY = {
    "prompt_id": "P9", "domain": "support agent",
    "planted": [
        {"category": "restated_capability", "line": ln("You are a helpful")},
        {"category": "duplicate", "lines": [ln("Verify the account before"), ln("| verify")],
         "phrase": "Verify the account before discussing billing"},
        {"category": "emphasis", "line": ln("IMPORTANT"), "tokens": ["IMPORTANT!!!", "MUST ALWAYS"]},
        {"category": "vague_contract", "line": ln("Be careful")},
        {"category": "conflict", "lines": [ln("Keep replies"), ln("Explain every")]},
        {"category": "unguarded_input", "line": ln("Quote the help-center")},
        {"category": "missing_contract", "depends_line": ln("Escalate refunds"), "fact": "the refund limit"},
        {"category": "work_order_unclear", "line": ln("Always suggest")},
        {"category": "work_order_unclear", "line": ln("Add a friendly")},
        {"category": "work_order_unclear", "line": ln("Offer a satisfaction")},
        {"category": "restriction", "line": ln("Never reveal")},
        {"category": "restriction", "line": ln("Do not promise")},
    ],
    "traps": {
        "generic_contract": {"line": ln("Refunds over the limit"), "tokens": ["billing_high"]},
        "reference_block": {"start": ln("```json") + 1, "end": LINES.index("```", ln("```json"))},
    },
}


def test_valid_prompt_and_key_pass():
    assert validate(TEXT, KEY) == []


def test_blank_line_reference_fails():
    key = copy.deepcopy(KEY)
    key["planted"][0]["line"] = 2
    assert any("out of range or blank" in e for e in validate(TEXT, key))


def test_missing_category_fails():
    key = copy.deepcopy(KEY)
    key["planted"] = [p for p in key["planted"] if p["category"] != "vague_contract"]
    assert "vague_contract: 0 entries; want exactly 1" in validate(TEXT, key)


def test_emphasis_token_not_on_its_line_fails():
    key = copy.deepcopy(KEY)
    key["planted"][2]["tokens"] = ["SHOUTING"]
    assert any("SHOUTING" in e for e in validate(TEXT, key))


def test_trap_listed_as_planted_fails():
    key = copy.deepcopy(KEY)
    key["traps"]["generic_contract"]["line"] = ln("Be careful")
    key["traps"]["generic_contract"]["tokens"] = ["careful"]
    assert "generic_contract: its line is also listed as planted" in validate(TEXT, key)


def test_too_short_prompt_fails():
    assert any("want 250-600" in e for e in validate("one two three\n", KEY))


def test_generic_contract_without_an_identifier_fails():
    key = copy.deepcopy(KEY)
    key["traps"]["generic_contract"]["tokens"] = ["the tag"]
    assert "generic_contract: no token looks like a product-specific identifier" in "\n".join(validate(TEXT, key))


REJECTED_IDENTIFIERS = ["day-to-day", "read-only", "e.g.", "end-to-end", "environment variable"]
ACCEPTED_IDENTIFIERS = ["PRICING_RULES", "record_key", "inv_ingest_v3", "schema_version",
                        "Billing_Escalation_L2", "2026-04", "camelCaseField", "config/app.yaml",
                        "settings.json"]


@pytest.mark.parametrize("token", REJECTED_IDENTIFIERS)
def test_identifier_rejects_ordinary_hyphenated_or_generic_words(token):
    assert not IDENTIFIER.search(token)


@pytest.mark.parametrize("token", ACCEPTED_IDENTIFIERS)
def test_identifier_accepts_product_specific_identifiers(token):
    assert IDENTIFIER.search(token)
