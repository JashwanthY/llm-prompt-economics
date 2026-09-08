# Skills

Three skills, deliberately separate because they answer different questions.

| skill | question it answers | needs to run your task? |
|---|---|---|
| **`prompt-contract`** | *What should go in my system prompt, and what shouldn't?* | no |
| **`guidance-audit`** | *Which lines of my existing prompt are actually doing anything?* | yes |
| `system-prompt-writing` | *Which prompting techniques raise accuracy on my task?* | no |

`prompt-contract` is the principle; `guidance-audit` is the measurement that
settles a case the principle cannot decide by reading. Use the first when
writing, the second when trimming.

## A caveat on `system-prompt-writing`

That skill predates the others and rests on a different study. Two of its
headline effect sizes should be treated as unreliable until re-derived: on
inspection, one rule's control arm scored 0.000 on all 15 models measured, so
its reported effect is determined by the arm's construction rather than by the
model, and a second shows the same pattern on 9 of 15. Both effect sizes have now been withdrawn from the skill and marked
directional; the advice they supported is retained on its own reasoning. Prefer
`prompt-contract` for guidance on what to include.
