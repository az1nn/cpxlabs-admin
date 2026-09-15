# Analysis: Git Publisher V8

## Scope reviewed

V8 introduces the first authority layer allowed to mutate Git publication state after the V3/V5/V6/V7 execution chain. The review focused on preserving the authority boundary established by ADR-0024 while proving that publication consumes exact fresh V7 evidence rather than treating validation success as timeless approval.

## Implementation candidate

The completed implementation candidate is commit `1dbf33e58a3f3f7d7166fb0cb806d48321be8430`.

It passed all required repository gates on that exact SHA:

- Spec Kit #397 — success
- Engineering Graph #339 — success
- Product CI #743 — success
  - migrations, typecheck, unit tests and build — success
  - Storybook component/accessibility tests — success
  - Playwright E2E — success

Engineering Graph #339 also re-ran the existing V1–V7 offline/unit/worktree, isolation, graph sync, V2 context, V3 execution and V4 GraphRAG checks without regression.

## Authority chain

```text
V3 active allocation
        |
        v
V5 successful execution evidence
        |
 optional V6 ownership
        |
        v
V7 passed + stable workspace evidence
        |
 exact validationId + current fingerprint match
        v
V8 Git Publisher
  | commit once
  | non-force push
  | open/reuse PR
  v
human review / merge boundary
```

V8 does not inherit any authority beyond the three publication phases. PR approval/merge, Task completion, lease release, worktree cleanup and Neo4j mutation remain outside V8.

## Closed gaps

1. Publication refuses validation evidence that does not exactly match the active allocation.
2. Workspace revision and V7 fingerprint are rechecked immediately before any Git mutation.
3. Empty publication diffs are rejected.
4. Git and GitHub CLI operations are argv-based with `shell=False`.
5. The publication branch must equal the active allocation branch and `origin` must resolve to the configured GitHub repository.
6. Commit construction records the exact commit SHA and verifies the validated revision as its parent.
7. Push is limited to the allocation branch and contains no force/force-with-lease path.
8. PR creation uses explicit repository/base/head/title/body inputs and reuses one existing open PR instead of duplicating it.
9. Durable publication records distinguish preflight, commit, push, PR and failure state so interrupted runs can resume without creating a second commit.
10. CLI routing is integrated into the composed Engineering Graph entrypoint.
11. Tests explicitly prove stale workspace rejection, no-shell command execution, non-force push, commit→push→PR progression and resume without duplicate commit.

## Divergence and resolution

The initial V8 branch contained the publisher runtime, CLI and tests but the composed `runner_entry.py` integration could not be written through the repository connector. The PR remained draft and no freeze was claimed.

A later minimal, normal contents-API update was accepted. Commit `62fe472390ce717a3e8c5cce011eea0c1b7138fe` registered `publication-run`, `publication-resume` and `publication-status` in the local command entrypoint. Additional hardening tests were then added before selecting the final implementation candidate.

This was an integration-path issue, not an authority relaxation: no force ref update or indirect bypass was used.

## Residual risks and explicit boundaries

- Publication records are local derived evidence and are not signed attestations.
- V8 relies on the local `git` and GitHub `gh` executables plus credentials inherited from the environment.
- V8 is GitHub-specific; provider abstraction is intentionally deferred.
- A remote branch may change outside the local process after publication. V8 never force-pushes to reconcile such drift.
- PR review and merge remain human/provider actions outside V8.
- Successful publication intentionally leaves the active allocation/lease/worktree lifecycle unchanged. Canonical Task completion and cleanup require a separate future policy/spec decision.

## Convergence decision

The implementation satisfies `SPEC-016-GIT-PUBLISHER` without expanding into merge, completion or cleanup authority. The final documentation commit containing `convergence.md` is the V8 freeze candidate and must independently pass Spec Kit, Engineering Graph and Product CI before PR #24 can become Ready for Review.
