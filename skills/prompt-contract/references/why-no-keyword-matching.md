# Why this skill does not classify lines mechanically

Two earlier versions of `audit.py` tried to decide, in code, which lines of a
prompt were generic advice and which were project requirements. Both failed, in
opposite directions, and the record is kept here because the failure is
instructive rather than embarrassing.

**Attempt 1 — detect contract lines by shape.** A regex looked for
identifier-ish tokens: `snake_case`, `camelCase`, hyphenated terms, filenames.
It classified **46 of 61 lines of pure generic guidance as contract**, because
`prefers-reduced-motion` is hyphenated and looks exactly like an identifier.

**Attempt 2 — detect guidance by keyword.** A library of ~19 signatures matched
known phrases (`aria-label`, `rem units`, `prefers-reduced-motion`). On a test
prompt with known ground truth it recognised **5 of 8** genuine guidance lines,
and — worse — flagged this line as deletable generic advice:

> `Every interactive control must carry an aria-label equal to its action_id from actions.json.`

That is a contract line. It names a field and a file that exist only in that
project. It was flagged because it contains the literal string `aria-label`.
In the same run, `Add ARIA roles to custom components` — which *is* generic
advice — was missed, because "ARIA roles" was not in the keyword list. The
matcher caught the wrong aria line and missed the right one.

## Why no third attempt will work

`prefers-reduced-motion` and `action_id from actions.json` are **lexically
identical**: both are hyphenated or underscored technical tokens embedded in an
imperative sentence. Nothing in the surface text separates them.

What separates them is meaning. One is a public web standard the model already
knows; the other is a fact that exists nowhere outside this repository. A
capable model knows which is which on sight. A regex never will, because the
distinction is semantic and the regex only sees characters.

So classification is the agent's job, and the scripts do not attempt it. The
scripts do the part the agent is bad at: counting occurrences across many
generated artifacts and normalising for size.
