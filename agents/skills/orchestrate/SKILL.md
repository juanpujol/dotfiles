---
name: orchestrate
description: Orchestrate a coding task across Herdr panes. Haiku codes and browser-verifies, Astra reviews with unslopify, you plan and verify.
disable-model-invocation: true
argument-hint: "<task or issue> [haiku=<agent>] [astra=<agent>] [slug=<name>] [unslopify=<path>]"
---

# Orchestrate

Arguments: `$ARGUMENTS`

You are the **orchestrator**. You do not code. You plan, delegate, review, and verify. Your tokens are expensive; Haiku's are cheap. Every edit under `src/`, `scripts/`, `packages/`, `apps/`, or a config file goes to Haiku as a brief, even when the user says "fix X now". Only an explicit "you do it here" overrides, and only for the named file. Planning artifacts (board, briefs, docs, memory) are yours.

## Setup

1. **Check Herdr.** `test "${HERDR_ENV:-}" = 1`, else say you are not in Herdr and stop. Load the `herdr` skill for CLI syntax.
2. **Parse arguments.** Free text is the task (an issue number means read the issue first; its acceptance criteria are the spec). `key=value` tokens override defaults:

   | Key | Default |
   |---|---|
   | `haiku` | the agent in `$HERDR_TAB_ID` whose name starts with `haiku` |
   | `astra` | the agent in `$HERDR_TAB_ID` whose name starts with `astra` |
   | `slug` | issue number as `i<N>`, else a kebab-case task name |
   | `unslopify` | `/Users/juan/Code/@laiki/laiki2/.agents/skills/unslopify/SKILL.md` |

3. **Resolve panes.** `herdr agent list`, filter to `tab_id == $HERDR_TAB_ID`, exclude `$HERDR_PANE_ID`. Never spawn, close, or rename panes. If a role is missing or matches more than one agent, ask the user which pane and stop.
4. **Open the board.** Create `/tmp/<slug>/BOARD.md`: spec, slices in priority order, status per slice, open decisions. It is Haiku's single source of truth. Fold every later user remark into the board (reprioritize, dedupe, resolve conflicts) instead of forwarding it raw.

Done when: both agent names are resolved, the spec is written, and the board lists every slice.

## Per-slice loop

Run one slice at a time.

1. **Brief Haiku.** Write `/tmp/<slug>/BRIEF-<n>.md` and prompt Haiku to read it and report to `/tmp/<slug>/REPORT-<n>.md`. Every brief carries:
   - the slice scope, the files to touch, and what is out of scope
   - the **test budget**: each test names the acceptance criterion it protects; one file per subject; test lines <= production lines, ratio reported
   - "Never commit, stash, reset, or checkout. Never open an interactive question; decide within this brief or stop and write the question in your report."
   - "Run `bun lint:changed` and only the affected test files, one at a time."
   - for UI changes: "Verify in the browser with the `agent-browser` skill (session `laiki`, login via `bun scripts/dev/browser-login.ts`). Screenshots at 1440 and 390, light and dark, paths listed in the report. Never start or stop dev servers; if the stack is down, stop and report."
2. **Monitor.** `herdr agent wait <haiku>`. On `blocked`, read the pane, tell the user what the prompt is in one line, and wait. Never answer a worker's permission prompt.
3. **Verify Haiku.** The report says where to look, never what is true. Read the diff yourself, rerun the claimed test file, open every screenshot. Check for drift from the brief. Send fixes back as a new brief and repeat until the slice is right.
4. **Review with Astra.** Prompt Astra to use the unslopify skill at the `unslopify` path in report-only mode (skip its fix step). The spec is the brief; the scope is the unstaged diff. Astra also rates each new test keep, merge, or cut. Astra writes `/tmp/<slug>/REVIEW-<n>.md`.
5. **Verify Astra and reach consensus.** Astra always finds something. Reproduce every finding in the source yourself and sort it into confirmed (fix), not an issue (drop, with the reason), or a judgment call. Send your triage back to Astra and talk it out until you agree. If a round turns up only theory or padding, the slice is ready. Disagreements still open after two rounds go to the user as one line each.
6. **Fix and close.** Confirmed findings go to Haiku as a fix brief, which goes through steps 2 and 3 again. When the slice is approved, Haiku stages exactly that slice (`git add <files>`), so the unstaged diff is always the next slice. Update the board.

Done when: the diff is verified by you, Astra's findings are triaged to consensus, the browser screenshots are checked by you, and the slice is staged.

## Finish

Report to the user: slices done, the Astra triage (confirmed, dropped, open), test ratio, screenshot paths, and anything waiting on them. Commits, pushes, PRs, and merges happen only when the user asks.
