# Skills

| skill | question it answers | needs to run your task? |
|---|---|---|
| **`prompt-contract`** | *What should be in my system prompt, and which of its lines are actually doing anything?* | to measure, yes; to classify, no |
| `system-prompt-writing` | *Which prompting techniques raise accuracy on my task?* | no |

`prompt-contract` covers both writing a prompt and auditing an existing one: it
classifies the lines, runs the task with and without the generic guidance,
buckets each line by whether the model's output actually changes, and reports
the token and latency effect of the trim. It never deletes anything itself --
lines that survive are features being bought, and that call belongs to the owner.

## A caveat on `system-prompt-writing`

That skill predates this work and rests on a different study. Two of its
headline effect sizes have been withdrawn and marked directional: one rule's
control arm scored 0.000 on all 15 models measured, so its reported effect was
fixed by the arm's construction rather than measured from the model, and a
second showed the same pattern on 9 of 15. The advice they supported is retained
on its own reasoning; the magnitudes are not.
