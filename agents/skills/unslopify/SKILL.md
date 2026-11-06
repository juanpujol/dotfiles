---
name: unslopify
description: Strip AI slop from the session's work — trace every diff hunk to the original issue or request, cut unrequested scope, speculative abstraction, and convention drift. Use when the user says unslopify, deslop, or asks to clean up what the agent built this session.
---

# Unslopify

Audit the session's entire diff against the **spec** — the original issue or request — and cut everything the spec does not warrant. Agents drift: they invent problems, add speculative flexibility, and solve things nobody asked for. This skill reverses that drift. The bias is deletion: the best diff is the smallest one that satisfies the spec.

**Warrant** is the operating word. Every hunk needs a warrant — a line in the spec, a locked decision, or a mechanical necessity (types, imports, a test for spec'd behavior) that requires it. No warrant → slop candidate.

## Process

### 1. Establish the spec

- Branch references an issue (`iN` branch, `Closes #N` in a commit or PR) → `gh issue view N` and read the body plus locked-decision comments. The issue is the acceptance criteria.
- No issue → the user's original request in this conversation is the spec. Use the *first* statement of the task, not the accumulated scope of the session.
- Work predates this conversation (multi-day branch) → check for an open PR (`gh pr view --json title,body`) and the branch's first commit message. If no spec source exists anywhere, ask the user to state it — never reverse-engineer the spec from the diff itself, that blesses the drift.
- Locked decisions settle intent. Missing rationale in code ≠ missing decision.

Done when: you can state the spec in 1–3 sentences and would bet on it.

### 2. Inventory the branch

The scope is everything since the branch forked — days of agent commits included — and nothing before it:

```bash
BASE=$(git merge-base HEAD dev 2>/dev/null || git merge-base HEAD main)
git log --oneline --reverse "$BASE"..HEAD   # every commit on this branch, oldest first
git diff "$BASE"..HEAD --stat               # cumulative net diff since the fork point
git status --short                          # uncommitted + untracked files count too
```

`merge-base` is the branching commit; `BASE..HEAD` can never walk past it. Read the commit list first — messages carry spec references (`Closes #N`) and show when drift entered. Then audit the **cumulative diff**, not commit-by-commit: changes a later commit reverted cancel out, only what survives matters.

Read every changed hunk and every new file in that diff. New `.md` files, scratch scripts, and new helpers are the highest-yield slop sites.

Fix the working tree only — never rebase, amend, or rewrite the branch's commits. Cleanup lands as new changes on top.

Done when: every commit message is read and every changed/new file in the cumulative diff is read, not skimmed.

### 3. Trace every hunk

Classify each hunk:

- **Required** — the spec names it.
- **Supporting** — mechanically necessary for a required change (type updates, imports, tests covering spec'd behavior).
- **Unwarranted** — everything else. This is the slop candidate list.

Caution: hunks the user hand-edited are not slop — when authorship is unclear and the change looks deliberate, ask instead of cutting.

**Tests get their own pass.** Agents over-test more than they over-build.

- Map each new test to an acceptance criterion or locked decision. If the issue lists acceptance tests, unmapped tests are candidates.
- Ratio smell: added test lines more than ~1.5× added production lines means start the audit with the tests.
- For every assert, grep for an existing test that already owns that behavior.
- Run each test through the two questions and patterns under Test slop in the taxonomy.

Done when: every hunk has one of the three labels.

### 4. Match unwarranted hunks against the taxonomy

Check each unwarranted hunk (and required hunks too — in-spec code can still be over-built) against [TAXONOMY.md](TAXONOMY.md). It encodes this codebase's conventions: Result pattern, layer separation, schema-first types, logger, naming.

### 5. Remediate

**Report-only mode.** If the arguments say "report only" (or another agent still owns the tree), skip steps 5 and 6. Output the step 7 report as a table: item, file, verdict (cut / trim / keep), reason. Write it so it can be pasted into a brief for another agent without further editing.

Two lanes:

- **Mechanical slop → fix directly.** Dead code, comment slop, artifact files, defensive bloat, convention drift, verbose names, single-use wrappers. Deletion and inlining only — behavior of in-spec code must not change. A runtime guard is only slop when the value's type is enforced at the boundary (see Defensive bloat in the taxonomy). If tracing it lands on a cast, keep the guard and move on.
- **Scope drift → decision table.** A whole behavior/feature/option the spec never asked for might still be wanted. Never silently delete it. Present one table:

| # | What it is | Where | Spec says | Recommend |
|---|-----------|-------|-----------|-----------|
| 1 | Retry-with-backoff on webhook fetch | `webhook.service.ts:88` | not mentioned | cut |

Recommend per row (default: cut). Apply only what the user picks.

**Complexity is never the fix.** If removing slop seems to require restructuring, new abstractions, or "a better design" — stop and flag it. Simplify means cut, not restructure. Complexity gets brainstormed with the user first, always. If the solution's overall *shape* looks wrong (far more files than the spec warrants), offer the `clean-room` skill instead of restructuring here.

### 6. Verify

- `bun lint:changed`
- Affected test files only (`bun test:integration <file>` per file; never the full suite).
- If you cut a runtime guard, first add the input it guarded against to the affected test. If the test still passes without the guard, the guard was slop; if it throws, put the guard back.
- Never touch `scripts/checks/*`, hooks, or add any lint suppression to make this pass — fix the code or report the conflict.

Done when: lint and affected tests are green, or the failure is reported verbatim.

### 7. Report

Lead with numbers: lines deleted, files removed, hunks cut vs kept. Then the decision table (if any rows remain), then anything flagged for brainstorm. Do not commit — the user commits.
