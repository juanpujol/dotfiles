---
name: orchestrate
description: Orchestrate a coding task across Herdr panes with three roles. The orchestrator plans and verifies, the worker codes, the reviewer reviews for real defects and challenges the orchestrator's plans.
disable-model-invocation: true
argument-hint: "<task or issue> [worker=<pane>] [reviewer=<pane>] [slug=<name>]"
---

# Orchestrate

Arguments: `$ARGUMENTS`

## Roles

| Role | Who | Does | Never |
|---|---|---|---|
| **Orchestrator** | you | Owns the spec, board and briefs. Plans, delegates, verifies every claim, triages review findings, talks to the user. | Edits code. Every edit to source, scripts or config goes to the worker as a brief, even when the user says "fix X now". Only an explicit "you do it here" overrides, for the named file only. Planning artifacts (board, briefs, docs, memory) are yours. |
| **Worker** | the pane resolved for `worker` (e.g. Sol, Haiku) | Implements briefs, runs the affected tests and lint, browser-verifies UI, commits and pushes when the brief says so. | Decides scope, answers its own open questions, bypasses validation. |
| **Reviewer** | the pane resolved for `reviewer` (e.g. Astra) | Reviews for **real defects** first, slop second (see Review). Challenges the orchestrator's plans before work starts. Exchanges reasoning with the orchestrator until they agree. | Edits, stages or commits. It reports; the worker fixes. |

The reviewer is a partner, not a lint pass. Use it in both directions: ask it to attack a plan before you brief the worker, and expect it to push back on your triage.

## Setup

0. **Load the project extension.** If the repo has a `*-orchestrate` skill (`.agents/skills/` or `.claude/skills/`, e.g. `laiki-orchestrate`), read it now. It adds project rules to every section below and overrides this skill where they conflict.
1. **Check Herdr.** `test "${HERDR_ENV:-}" = 1`, else say you are not in Herdr and stop. Load the `herdr` skill for CLI syntax.
2. **Parse arguments.** Free text is the task (an issue number means read the issue first; its acceptance criteria are the spec). `key=value` tokens override defaults:

   | Key | Default |
   |---|---|
   | `worker` | the single agent in `$HERDR_TAB_ID` whose footer model is a worker model (Sol, Haiku) |
   | `reviewer` | the single agent in `$HERDR_TAB_ID` whose footer model is Astra |
   | `slug` | issue number as `i<N>`, else a kebab-case task name |

3. **Resolve panes.** `herdr agent list`, filter to `tab_id == $HERDR_TAB_ID`, exclude `$HERDR_PANE_ID`. Before assigning any role, run `herdr pane read <pane> --source recent-unwrapped --lines 5` on every candidate and read the model in its footer. The role follows the footer model, never the herdr agent name (a pane named `sol-837` ran Astra). Record each role as pane ID plus model on the board and tell the user the mapping. Also record the worker's workspace ID, read from `herdr pane get <worker pane>` (never from a worker's environment); every brief writes it literally wherever `<workspace_id>` appears. Never spawn, close or rename panes. A missing or ambiguous role: ask the user and stop.
4. **Open the board.** `/tmp/<slug>/BOARD.md`: spec, locked decisions (with who decided), **user intent**, slices in priority order, status per slice, open questions. Fold every later user remark into the board instead of forwarding it raw.
   - **User intent** is a table of every product or design direction the user gave, quoted verbatim with the date (e.g. "like Supabase's Table Editor: dataset selector, table list, tabs, SQL tab"). Each item has a status: `planned (slice N)`, `deferred (user agreed, date)` or `done (evidence path)`. Only the user can defer an item; "later slice unless trivial" is not agreement.

Done when: every role maps to a pane ID by footer model, the spec and locked decisions are written, and the board lists every slice.

## Per-slice loop

Run one slice at a time.

1. **Plan, then let the reviewer attack it** (non-trivial slices, any model-facing text, contracts, env or schema changes). Write the plan in the brief draft and ask the reviewer for a short design review: wrong assumptions, platform constraints, cheaper alternatives, missing edge cases. Settle disagreements before the worker starts. Skip for mechanical slices.
2. **Brief the worker.** `/tmp/<slug>/BRIEF-<n>.md`; worker reports to `/tmp/<slug>/REPORT-<n>.md`. Every brief is **self-contained** (`/tmp` can be wiped overnight: inline the rules, decisions and test lists it needs; never "see BRIEF-x.md"). It carries:
   - scope, files to touch, what is out of scope, and the locked decisions that apply
   - the user-intent items this slice touches, quoted, as **requirements**. Never turn a user direction into a choice for the worker ("X or Y, decide from the standard"). Standards decide how to build an intent item, never whether to build it.
   - verification data that exercises every intent item (a list needs 3+ entries, a panel needs a clickable row); data that hides the feature is not verification
   - the **test budget**: each test names the acceptance criterion it protects; one file per subject; test lines <= production lines, ratio reported
   - "Never stash, reset, checkout other branches, force anything, or `git add -N`. Commit only when this brief says so. Never open an interactive question; decide within this brief or stop and write the question in your report."
   - "Run the project's changed-files lint and only the affected test files, one at a time."
   - "Communicate in English only: progress notes, replies and the report. Other languages only when quoting UI copy."
   - for UI changes: "Verify in the browser with the `agent-browser` skill against this checkout's own stack. If a `server` tab for this checkout is already running, reuse it (check it is still ready) instead of starting another. Otherwise start it visibly, never in the background: `herdr tab create --workspace <workspace_id> --cwd "$PWD" --label server --no-focus`, then check that the returned `.result.tab.tab_id` starts with `<workspace_id>:` (if not, close that tab and stop), then `herdr pane run <root_pane.pane_id> "<dev command>"`. Wait until the server is ready (its ready line in that pane, then the URL answers) before any login or browser step. Never use `$HERDR_WORKSPACE_ID`, `$HERDR_TAB_ID` or `$HERDR_PANE_ID` in a worker: Codex runs commands through a shared daemon whose snapshot carries another pane's IDs. Screenshots at 1440 and 390, light and dark, paths listed in the report. Keep the server running after the checks: later slices reuse it. Stop it (`herdr pane send-keys <pane> ctrl+c`, then `herdr tab close <tab_id>`) only when the orchestrator's brief says no more browser work is planned. Never touch another checkout's dev server or browser session." The project extension supplies the dev command, URL, readiness check and login.
3. **Monitor.** Ending your turn stops monitoring. After prompting a partner, stay in the turn: `herdr agent wait <pane> --timeout 590000` (milliseconds; background it if a user message may arrive), then `herdr agent get <pane>` and check the report file. Short status lines to the user between waits, never a turn end. On `blocked`, read the pane, tell the user the prompt in one line, keep waiting. Never approve a worker's permission prompt; a prompt that breaks the brief may be declined, then re-prompt with the allowed alternative. Valid turn ends: the finish report, a question only the user can answer while every partner is idle, or the user telling you to stop.
4. **Verify the worker.** The report says where to look, never what is true. Read the diff, rerun the claimed test file, open every screenshot, check drift from the brief. Then check **intent**: for every user-intent item the slice touches, mark present or missing against the screenshots (and the user's reference image, if any). The brief is not the spec when it drifted from the user; a missing item is a defect even if the brief allowed it. Fixes go back as a new brief.
5. **Review, twice, independently.** Prompt the reviewer with the user-intent table and the brief as spec, and the slice diff as scope. It writes `/tmp/<slug>/REVIEW-<n>.md` (see Review for what it covers). In parallel, run the same review yourself: the project's PR review skill and the `unslopify` skill (report-only) on the same scope, without reading the reviewer's report first. Write yours to `/tmp/<slug>/REVIEW-<n>-orchestrator.md`.
6. **Compare notes to consensus.** Put both reviews side by side. Reproduce every finding from either side in the source: confirmed (fix), not an issue (drop, with the reason), or judgment call. Send the merged triage to the reviewer and argue it out; either side may overturn the other's drops with evidence. Only the agreed fix list goes to the worker. A round with only theory or padding means the slice is ready. Still open after two rounds: one line each to the user.
7. **Fix and close.** Confirmed findings go to the worker as a fix brief (steps 3-4 again). When approved, the worker stages or commits exactly that slice, per the brief. Update the board.

Done when: you verified the diff and screenshots, review findings are triaged to consensus, and the slice is staged or committed.

## Review

The reviewer runs these lenses, in order, and reports one table (finding, file:line, failure path, verdict fix/trim/cut/keep):

0. **Intent.** Every user-intent item the slice touches: present, missing, weakened, or silently deferred. Report gaps even when the brief allowed them; the orchestrator's brief is a suspect too.
1. **Correctness**, via the project's PR review skill if it has one: trace each failure path beyond the hunk (trigger, mechanism across named files, consequence). Run it first so automated PR reviewers find nothing.
2. **Contracts the code relies on.** Every instruction in model-facing text (tool guidance, playbooks, prompts) names operations that can actually succeed for that caller: check each against the operation's description, permissions and the data it returns. Env vars: schema and build config. API/RPC schemas, duplicate i18n copy, generated files.
3. **Tests:** each new test maps to an acceptance criterion; rate keep, merge or cut; flag tests that pin prose instead of behavior.
4. **Slop, via the `unslopify` skill** (report-only): unrequested scope, speculative abstraction, convention drift, leftovers.

## Before a PR

Run a full-branch review (all four lenses, scope `git diff origin/<base>...HEAD`) and triage it to consensus before the push. The PR opens only when the user asked for it, after the pre-push hooks pass without bypass.

## Rules for the orchestrator

- Background watchers or waits are recorded on the board (command and path) so a compaction or restart resumes monitoring first.
- A user question is a question: answer it, recommend, and wait. Never turn a frustrated "why is X here?" into a brief.
- Product, copy and scope calls go to the user (AskUserQuestion with a recommendation). Standard-covered decisions you make yourself and say which standard.
- Commits, pushes, PRs and merges happen only when the user asks. Never merge.
- Follow the project's documented standards and prefer its established libraries over hand-rolled code. Simplest, most concise change that meets the spec; never over-engineer or over-test.

## Finish

Report to the user: slices done, the user-intent table (present / missing / deferred, with evidence), review triage (confirmed, dropped, open), test ratio, screenshot paths, and anything waiting on them. Every per-slice status message to the user also lists the intent items that slice touched.
