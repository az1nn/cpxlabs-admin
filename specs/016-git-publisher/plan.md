# Implementation Plan: Git Publisher V8

## Architecture

V8 is a local engineering-only publication state machine layered after V7:

```text
V3 active allocation
        |
V5/V6 execution evidence
        |
V7 passed + stable workspace evidence
        |
        v
V8 publisher record
  started -> committed -> pushed -> pr_opened
                    \-> failed -> resumable
```

Authority flows only from canonical Git-backed configuration/evidence and explicit operator inputs toward publication. Publication state never flows back into Task completion or architecture truth.

## Components

1. `publisher.py`
   - immutable/versioned publication record;
   - evidence freshness checks;
   - Git/GitHub remote preflight;
   - commit/push/PR state machine;
   - recovery/resume semantics;
   - atomic disposable persistence.
2. `publisher_cli.py`
   - `publication-run`;
   - `publication-resume`;
   - `publication-status`.
3. `runner_entry.py`
   - route V8 local commands without contaminating legacy graph CLI.
4. tests
   - record/state invariants;
   - stale/mismatched evidence rejection;
   - command construction and no-force invariants;
   - resume semantics;
   - CLI routing.
5. docs
   - ADR-0024;
   - architecture/operator workflow;
   - scoped `engineering-graph/AGENTS.md` update.

## Safety decisions

- Current V7 fingerprint must match before the first Git mutation.
- `git add -A`, `git commit`, `git push`, and `gh pr create` are subprocess argv with `shell=False`.
- Only `origin` is used; its repository identity must match configured `owner/repo`.
- Push is ordinary non-force push of the allocation branch.
- No merge API/CLI exists in V8.
- Publication is phase-persisted and resumable after commit/push failures.
- Secrets remain environment-only.

## Validation

Required convergence gates on one final HEAD:

1. Spec Kit workflow.
2. Engineering Graph workflow, including full offline V1–V8 tests.
3. Product CI.

No content changes are allowed after the final green freeze HEAD.
