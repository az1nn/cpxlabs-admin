# Implementation Plan: Post-Publication Lifecycle V9

## Scope

Implement a local reconciliation/finalization layer after V8 publication and human PR merge, plus repository-owned continuation/human-gate policy.

## Architecture

1. Read one V8 `PublicationRecord`.
2. Validate matching active V3 allocation/lease.
3. Query PR state with `gh pr view ... --json ...` using argv and `shell=False`.
4. Require `mergedAt` and merge commit.
5. Fetch configured base branch and verify merge commit reachability.
6. Read canonical `specs/<feature>/tasks.md` from the refreshed base using `git show <base>:<path>`.
7. Require exactly one matching checked Task ID.
8. Produce read-only reconciliation result.
9. On explicit finalize, persist receipt, release lease, and optionally remove a clean worktree.
10. Preserve idempotency through versioned receipt state.

## New modules

- `engineering-graph/src/engineering_graph/post_publication.py`
- `engineering-graph/src/engineering_graph/post_publication_cli.py`
- updates to `runner_entry.py`

## Tests

- record schema/roundtrip/malformed rejection;
- open PR rejection;
- merged PR + unreachable merge rejection;
- canonical Task incomplete/ambiguous rejection;
- merged/canonical-complete reconciliation;
- explicit lease release;
- clean worktree removal;
- dirty worktree refusal;
- idempotent repeated finalize;
- CLI routing/JSON output;
- V1–V8 regression suite.

## Policy/docs

- `docs/ai/human-async-gates.md`;
- `docs/ai/chatgpt-project-instructions.md`;
- `docs/ai/context-handoff.md`;
- `docs/ai/session-handoff-template.md`;
- `AGENTS.md`;
- architecture/development docs.

## Freeze

Final readiness requires Spec Kit + Engineering Graph + Product CI green on the exact same final HEAD, with no subsequent content commit.
