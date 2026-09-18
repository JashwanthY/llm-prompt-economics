# Study B findings — bolt.diy "Old Default Prompt", Claude Code + prompt-contract

Source run: `experiments/skilleval/runs/B/B-claude-on/a1/` (turn 1 only; the file was not changed).

## Agent's reply, verbatim

## Prompt audit — prompt.md

**Summary:** This is a large, detailed system prompt for an AI app-builder (Bolt/WebContainer + Supabase + Expo). Most of the length is legitimate, project-specific contract (exact tag schemas, environment limits, migration format) that's cheap to keep. The real cost is four rules stated 2–4 times each, a direct contradiction on whether to generate Supabase types, a plan-before-answering instruction that collides with "don't explain unless asked," and a design/best-practices block that's almost entirely generic advice a competent model doesn't need spelled out.

### Numbers
| kind | lines | share |
|---|---|---|
| Contract | ~64 | 54% |
| Work orders | ~36 | 31% |
| Restrictions | ~18 | 15% |
| **Total** | ~118 | |

- **Size:** ~5,000 words (~6,500 tokens) — counted item-by-item, not exact
- **Contract share:** 54% — mixed
- **Issues:** 15 — 4 high · 8 medium · 3 low

### Findings

1. **Conflict** · high · L71 vs L213, L237
   > "Do not try to generate types for supabase." / "Use TypeScript generated types from the schema." / "Generate types from database schema."
   The prompt tells the model both to skip and to generate Supabase types. Whichever the model picks, it's guessing against an explicit contradiction.
   **Proposed:** see Needs your decision #1

2. **Conflict** · high · L253-257 vs L422
   > "Before providing a solution, BRIEFLY outline your implementation steps... Be concise (2-4 lines maximum)" vs "ULTRA IMPORTANT: Do NOT be verbose and DO NOT explain anything unless the user is asking for more information."
   One rule mandates a plan on every reply, the other forbids explaining unless asked. These can't both hold on a first response.
   **Proposed:** see Needs your decision #2

3. **Vague/dead contract** · high · L30
   > "CRITICAL: You must never use the "bundled" type when creating artifacts, This is non-negotiable and used internally only."
   No `"bundled"` type is defined anywhere among the documented `boltAction` types (`shell`/`file`/`start`), so this may be a leftover instruction from an older version, or reference internal tooling never explained here — the model can't act on it correctly either way.
   **Proposed:** see Needs your decision #3

4. **Unfilled template values** · high · L400-406
   > "FONT: undefined / COLOR PALETTE: undefined / FEATURES: undefined"
   If your app doesn't substitute these before the prompt is sent, the model is literally told the font is "undefined" and may echo or reason about that string.
   **Proposed:** see Needs your decision #5

5. **Duplicate (4x)** · medium · L24, L114, L344-349
   > "always write your code in full no partial/diff update" / "NEVER use diffs for migration files, ALWAYS provide COMPLETE file content" / "CRITICAL: Always provide the FULL, updated content of the artifact..."
   Same rule, three places.
   **Proposed:** keep L344-349 (most complete version); delete L24 and L114.

6. **Duplicate (3x)** · medium · L121-125, L222, L241
   > "ALWAYS enable row level security (RLS) for new tables" / "ALWAYS enable RLS for every new table" / "NEVER skip RLS setup for any table. Security is non-negotiable!"
   **Proposed:** keep L121-125 (has the example); delete L222 and L241.

7. **Duplicate** · medium · L290-297 vs L429-436
   > "Think HOLISTICALLY and COMPREHENSIVELY BEFORE creating an artifact..." repeated near-verbatim in `artifact_instructions` and again in `mobile_app_instructions`.
   **Proposed:** keep L290-297 (applies to all artifacts, mobile included); delete L429-436.

8. **Duplicate** · medium · L372 vs L477-478
   > "Bolt ALWAYS uses stock photos from Pexels..." stated identically in `design_instructions` and again in `mobile_app_instructions`.
   **Proposed:** keep L372; delete L477-478.

9. **Overlapping restriction, stated twice** · medium · L351 vs L414-416
   > "NEVER say something like 'You can now view X...'" and separately "NEVER say... 'Now that the initial files are set up, you can run the app.' INSTEAD: Execute the install and start commands on the users behalf."
   Same intent (don't tell the user to run it themselves — do it for them), two different wordings.
   **Proposed:** merge into L414-416, replace with: `NEVER tell the user to open a URL, run install/start commands, or "view the app" themselves — always execute those commands on their behalf via boltAction.` Delete L351.

10. **Duplicate** · medium · L32
    > "CRITICAL: You MUST always follow the <boltArtifact> format."
    Restates what the detailed `artifact_instructions` block (L282-362) already mandates precisely.
    **Proposed:** delete.

11. **Duplicate work order** · medium · L418
    > "IMPORTANT: For all designs I ask you to make, have them be beautiful, not cookie cutter. Make webpages that are fully featured and worthy for production."
    Restates the `design_instructions` opening goal (L365) almost word for word.
    **Proposed:** delete.

12. **Work orders to confirm** · medium
    Generic best-practice/aesthetic asks the model already defaults to; effect on this prompt is unverified — only a run shows whether they change output.
    - L230-234 (migration best practices: descriptive policy names, indexes, foreign keys)
    - L236, L238-239 (strong typing, type safety — separate from the types conflict in #1)
    - L365-398 (`design_instructions`: visual identity, layout, UX, color/typography, technical excellence — ~230 words of generic direction)
    - L459-461 (state management library choice)
    - L513-517 (performance: memo/useCallback/virtualized lists)
    - L536-539, L541-549 (component structure, form libraries, "design inspiration")
    **Proposed:** see Needs your decision #4

13. **Ambiguous/unverifiable ask** · medium · L224-227
    > "Test RLS policies by: 1. Verifying authenticated users... 2. Confirming unauthenticated users... 3. Testing edge cases..."
    The assistant writes code in one pass and doesn't execute tests — unclear what artifact this should produce (a test file? a comment? nothing?).
    **Proposed:** delete, or replace with a concrete ask like "add a code comment above each policy stating which access pattern it allows and denies" — needs your call.

14. **Restated capability** · low · L2
    > "an expert AI assistant and exceptional senior software developer with vast knowledge across multiple programming languages, frameworks, and best practices"
    **Proposed:** replace with: `You are Bolt, an AI assistant and senior software developer.`

15. **Emphasis for precision** · low · ~30 occurrences (e.g. L10, L20, L22, L26, L28, L65, L85, L113-114, L216-219, L290, L318, L322-325, L344, L422, L429)
    `CRITICAL:`, `IMPORTANT:`, `ULTRA IMPORTANT:` are used as a volume knob on ordinary rules rather than to flag exceptions, which trains the model to discount them everywhere, including the few places they matter.
    **Proposed:** strip the prefix word, keep the plain rule, on all instances not already covered by another finding.

### Keep as-is
- L34-59 "Available shell commands" — reference list, cheap, keep
- L73-82 data-preservation restrictions (no DROP/DELETE, no transaction control) — contract, essential
- L155-207 migration file example — reference template, cheap
- L216-219 auth restrictions (email/password only, no magic links/SSO, no custom auth table) — contract
- L249 allowed HTML elements list — contract, essential
- L303-342 `boltArtifact`/`boltAction` schema and ordering rules — contract, essential
- L410-412 "NEVER use the word 'artifact'" with example — restriction, clear and cheap
- L467-475 mobile "feature/content rich screens" requirements — high-value work order (this is the kind of specific ask that reliably shows up in output)
- L528 "Implement reduced motion alternatives for animations" — high-value work order
- L588-678 usage examples — reference, cheap

### Needs your decision
1. **Supabase types (L71 vs L213/L237):** should the model generate TypeScript types from the Supabase schema, or never touch them? Pick one; I'll delete the other two statements.
2. **Mandatory pre-solution plan (L253-280) vs "don't explain unless asked" (L422):** keep the 2-4 line plan on every response, or drop it in favor of terse-by-default? If kept, it needs a line saying it doesn't count as "explaining."
3. **"bundled" type (L30):** is this a real internal artifact type your app still checks for, or leftover from an earlier version? If real, it needs to say what it is and when it'd apply; if dead, delete it.
4. **Work-order bundle (finding 12):** which of these do you actually want enforced — keep the full design_instructions detail, trim it to a few high-value lines (like the reduced-motion one), or cut it and trust the model's defaults?
5. **Template placeholders (L400-406):** confirm your app fills FONT/COLOR PALETTE/FEATURES before sending, and skips the whole block when unset instead of sending literal "undefined".

### If every change is approved
- **Prompt:** ~5,000 → ~4,600 words (≈−8%), more if you also trim finding 12
- **Output:** down slightly on database/type-generation tasks (conflict removed, no more guessing); latency/output on design and mobile tasks depends on your answer to #4. Not measured on this prompt.

**Reply "apply all", "apply 1, 3, 4" or "skip", and answer the questions above.** The file has not been changed.

## Decision sheet

One row per finding from the reply above, for the owner to mark accept / reject / answer. Numbers, types, severities, line references, quotes and proposed changes are taken verbatim from the reply; nothing here is added or reordered.

| # | Issue type | Severity | Line ref | Quoted line | Proposed change |
|---|---|---|---|---|---|
| 1 | Conflict | high | L71 vs L213, L237 | "Do not try to generate types for supabase." / "Use TypeScript generated types from the schema." / "Generate types from database schema." | see Needs your decision #1 |
| 2 | Conflict | high | L253-257 vs L422 | "Before providing a solution, BRIEFLY outline your implementation steps... Be concise (2-4 lines maximum)" vs "ULTRA IMPORTANT: Do NOT be verbose and DO NOT explain anything unless the user is asking for more information." | see Needs your decision #2 |
| 3 | Vague/dead contract | high | L30 | "CRITICAL: You must never use the "bundled" type when creating artifacts, This is non-negotiable and used internally only." | see Needs your decision #3 |
| 4 | Unfilled template values | high | L400-406 | "FONT: undefined / COLOR PALETTE: undefined / FEATURES: undefined" | see Needs your decision #5 |
| 5 | Duplicate (4x) | medium | L24, L114, L344-349 | "always write your code in full no partial/diff update" / "NEVER use diffs for migration files, ALWAYS provide COMPLETE file content" / "CRITICAL: Always provide the FULL, updated content of the artifact..." | keep L344-349 (most complete version); delete L24 and L114. |
| 6 | Duplicate (3x) | medium | L121-125, L222, L241 | "ALWAYS enable row level security (RLS) for new tables" / "ALWAYS enable RLS for every new table" / "NEVER skip RLS setup for any table. Security is non-negotiable!" | keep L121-125 (has the example); delete L222 and L241. |
| 7 | Duplicate | medium | L290-297 vs L429-436 | "Think HOLISTICALLY and COMPREHENSIVELY BEFORE creating an artifact..." repeated near-verbatim in `artifact_instructions` and again in `mobile_app_instructions`. | keep L290-297 (applies to all artifacts, mobile included); delete L429-436. |
| 8 | Duplicate | medium | L372 vs L477-478 | "Bolt ALWAYS uses stock photos from Pexels..." stated identically in `design_instructions` and again in `mobile_app_instructions`. | keep L372; delete L477-478. |
| 9 | Overlapping restriction, stated twice | medium | L351 vs L414-416 | "NEVER say something like 'You can now view X...'" and separately "NEVER say... 'Now that the initial files are set up, you can run the app.' INSTEAD: Execute the install and start commands on the users behalf." | merge into L414-416, replace with: `NEVER tell the user to open a URL, run install/start commands, or "view the app" themselves — always execute those commands on their behalf via boltAction.` Delete L351. |
| 10 | Duplicate | medium | L32 | "CRITICAL: You MUST always follow the <boltArtifact> format." | delete. |
| 11 | Duplicate work order | medium | L418 | "IMPORTANT: For all designs I ask you to make, have them be beautiful, not cookie cutter. Make webpages that are fully featured and worthy for production." | delete. |
| 12 | Work orders to confirm | medium |  | (no single line quoted in reply) | see Needs your decision #4 |
| 13 | Ambiguous/unverifiable ask | medium | L224-227 | "Test RLS policies by: 1. Verifying authenticated users... 2. Confirming unauthenticated users... 3. Testing edge cases..." | delete, or replace with a concrete ask like "add a code comment above each policy stating which access pattern it allows and denies" — needs your call. |
| 14 | Restated capability | low | L2 | "an expert AI assistant and exceptional senior software developer with vast knowledge across multiple programming languages, frameworks, and best practices" | replace with: `You are Bolt, an AI assistant and senior software developer.` |
| 15 | Emphasis for precision | low | ~30 occurrences (e.g. L10, L20, L22, L26, L28, L65, L85, L113-114, L216-219, L290, L318, L322-325, L344, L422, L429) | (no single line quoted in reply) | strip the prefix word, keep the plain rule, on all instances not already covered by another finding. |

## Needs your decision

The agent's own questions, verbatim, in the order given:

1. **Supabase types (L71 vs L213/L237):** should the model generate TypeScript types from the Supabase schema, or never touch them? Pick one; I'll delete the other two statements.
2. **Mandatory pre-solution plan (L253-280) vs "don't explain unless asked" (L422):** keep the 2-4 line plan on every response, or drop it in favor of terse-by-default? If kept, it needs a line saying it doesn't count as "explaining."
3. **"bundled" type (L30):** is this a real internal artifact type your app still checks for, or leftover from an earlier version? If real, it needs to say what it is and when it'd apply; if dead, delete it.
4. **Work-order bundle (finding 12):** which of these do you actually want enforced — keep the full design_instructions detail, trim it to a few high-value lines (like the reduced-motion one), or cut it and trust the model's defaults?
5. **Template placeholders (L400-406):** confirm your app fills FONT/COLOR PALETTE/FEATURES before sending, and skips the whole block when unset instead of sending literal "undefined".

