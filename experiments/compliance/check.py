"""Count violations of the five stated house rules. Purely mechanical."""
import json, pathlib, re, sys

def check(p: pathlib.Path) -> dict:
    s = p.read_text(errors="replace")
    body = re.sub(r"<script\b.*?</script>", "", s, flags=re.S | re.I)
    m = {"file": p.name}
    # 1. no hardcoded hex colours.
    #
    # Two readings, both reported, because the rule as written is ambiguous and
    # picking one silently would be picking the flattering one:
    #   strict -- sentence 1, "never write a hardcoded hex colour": any hex.
    #   intent -- sentence 2, "define all colours as custom properties in :root
    #             and reference them with var()": a hex OUTSIDE :root.
    # An earlier version summed style+body; <style> is inside body, so every
    # hex was counted twice, and it also scored compliant :root definitions as
    # violations. Both bugs inflated the violation counts.
    root = re.search(r":root\s*\{(.*?)\}", s, re.S)
    hexes = lambda t: len(re.findall(r"#[0-9a-fA-F]{3,8}\b", t))
    m["hex_strict"] = hexes(body)
    m["hex"] = m["hex_strict"] - hexes(root.group(1) if root else "")
    # 2. no inline event handlers
    m["inline_handlers"] = len(re.findall(r'\son[a-z]+\s*=\s*["\']', body))
    # 3. every interactive element carries data-testid
    inter = re.findall(r"<(?:button|input|select|textarea|a)\b[^>]*>", body, re.I)
    m["interactives"] = len(inter)
    m["missing_testid"] = sum(1 for e in inter if "data-testid" not in e)
    # 4. every id begins with app-
    ids = re.findall(r'\sid="([^"]+)"', body)
    m["ids"] = len(ids)
    m["bad_id_prefix"] = sum(1 for i in ids if not i.startswith("app-"))
    # 5. no innerHTML
    m["innerHTML"] = len(re.findall(r"\.innerHTML\s*=", s))

    m["rules_broken"] = sum([m["hex"] > 0, m["inline_handlers"] > 0,
                             m["missing_testid"] > 0, m["bad_id_prefix"] > 0,
                             m["innerHTML"] > 0])
    m["rules_kept"] = 5 - m["rules_broken"]
    return m

if __name__ == "__main__":
    for p in sorted(pathlib.Path(sys.argv[1]).glob("*.html")):
        print(json.dumps(check(p)))
