# Slop Taxonomy — laiki2

Reference for step 4. Each category: what it looks like, and the fix. Fix column assumes the mechanical lane (delete/inline); anything bigger goes to the decision table or a brainstorm flag.

## Scope drift (decision-table lane)

The defining agent failure: solving problems the spec never named.

- New behavior, endpoint, option, flag, or config the issue doesn't mention.
- "While I was here" fixes to unrelated code.
- Handling of invented edge cases the spec (or the data model) rules out.
- Generalizing a fix beyond the reported case ("also applied it to the other three services").
- Unrequested performance work, caching, batching, memoization.

## Speculative abstraction

- Helper/wrapper with exactly one caller → inline it.
- Pass-through function that adds no logic → delete, call the target.
- Parameters, generics, or options only one call site uses with one value → hardcode.
- Interface/type union sized for futures that aren't in the spec → shrink to what's used.
- New file/module for something that fits in the existing one → merge back.
- Re-export shims → repoint imports directly, delete the shim.

## Naming

- Verbose context-repeating names: `createMemberWithTransaction` inside members service → `create`. The surrounding module IS the context.
- Names describing implementation instead of role.

## Defensive bloat

- try/catch around code that can't throw, or where the Result pattern already carries the error. Catch blocks use `catch (err)` + `log.error`.
- Re-validating input a Valibot schema already validated at the boundary.
- Null/undefined checks or narrowing on a value whose type is ENFORCED at the boundary: parsed by a Valibot/Effect schema, or produced by code you can read. A declared type is not proof. Before cutting a runtime guard, trace the value to where its type comes from. If that is `typedUnknown`, an `as` cast, `unknown` laundering, a JSON column, or a provider payload, the type is a cast and the guard stays. In this codebase `widgetConfigSchema.queries[].dataSource` and `.insights` are casts, and `dataConfig` read from `dashboard_widgets` is a JSON column.
- Fallback values for impossible states (`?? ""` on a required field).
- `unknown`/type-widening plus narrowing where the schema type was already exact. (`any` is never acceptable, but neither is laundering types through `unknown` without need.)

## Convention drift

New pattern where a codebase pattern exists:

- Throwing/returning ad-hoc errors instead of `Result<T, ServiceError>` with a `SERVICE_ERRORS` code.
- Localized/user-facing message strings crossing the API boundary instead of error codes + `translateApiError` in the UI.
- Supabase client created outside `src/lib/services/` (never in routes, loaders, components, server fns).
- Ad-hoc local types instead of `v.InferInput`/`v.InferOutput` from the `*.schema.ts` source of truth.
- `console.log`/`console.error` instead of `log.*` from the logger.
- Business logic in a component or route instead of a service; data transforms in the UI layer.
- One-off styled component instead of a `packages/ui` variant; reusable UI outside `src/components/common/`.
- New PL/pgSQL function/trigger where the service layer could do it.

## Comment slop

- Comments narrating what the next line does.
- Comments justifying the change to a reviewer ("this is safe because…", "fixed by using X").
- References to ADRs, decision docs, issue numbers inside code comments.
- Docstrings on trivial functions.
- Commented-out code.

Keep only comments stating a constraint the code can't show.

## Artifact slop

- Unrequested markdown: PLAN.md, NOTES.md, SUMMARY.md, scratch devlogs, docs/tasks entries nobody asked for.
- Scratch/debug scripts left in the tree.
- Leftover `log.debug`/temporary logging added while diagnosing.
- `.tmp`, fixture dumps, generated files that don't belong in git.
- Verification harnesses outside the test system: a bespoke script (psql runner, fixture checker, "verify-*.ts") that no test runner, CI job, or package script invokes. It proves something once and rots. Cut it; if it covers spec'd behavior, flag converting it into a real test.

## Test slop

Agents over-test. Every new test must answer two questions:

1. **What regression would this catch that no other test catches?** "Nothing" → cut.
2. **Would it break on a behavior-preserving refactor?** "Yes" → it tests implementation, cut or rewrite.

Patterns:

- Tests for unwarranted behavior (cut the behavior → cut its tests).
- Duplicate coverage of the same path across files.
- Over-mocked tests asserting mock wiring instead of behavior.
- Integration tests that don't drive the real pipeline.
- **Re-asserting a neighbor's contract.** A new test checks pre-existing behavior another test file owns (retry limits, redirect mode, request body shape). Grep for the owning test; if it exists, cut the assert. These break when an unrelated policy changes.
- **Impossible-failure tests.** A mock forces a throw the real dependency cannot produce (`crypto.randomUUID` throwing, a "never throws" helper throwing) to cover a defensive catch. Cut the guard and its test together; the pair is dead code with a witness.
- **Implementation-text assertions.** `toContain` / snapshot checks on generated SQL fragments, prompt sentences, log strings, or source text. They break on reformatting and prove no behavior. Replace with one execution-level test or cut.
- **Absence-of-nonexistent-code tests.** Asserting the code "never does X" when nothing in the code attempts X ("never parses HTML for status"). Cut.
- **Library-behavior tables.** Long loops of malformed inputs proving the schema library rejects `1.5`, `-1`, bad UUIDs. Keep one case per rule *we* wrote (tenant check, size cap, origin gate), not one per validator.
- **Same invariant at every layer.** Field stripping tested in the shared parser, again in the store, again in the handler. Test the logic once at the lowest layer, plus one test proving the wiring.
- **Piggybacked asserts.** A valid core test grows trailing asserts unrelated to its name. Trim the tail, keep the test.
- **Inverse-path checks.** "Success request does not trigger the error tap." The control flow makes it obvious; cut.

## Dead code

- Unused exports, imports, variables, branches.
- Unreachable code behind conditions that can't fire.
- Stale feature-flag branches from mid-session direction changes.
- Old implementation left beside its replacement.
