# Convergence: Git Publisher V8

## Outcome

V8 converges the validation-to-publication gap while preserving a hard human boundary at pull-request review and merge.

The final authority chain is:

```text
V3 allocation
   |
V5 execution
   |
optional V6 supervision
   |
V7 passed + stable workspace
   |
   v
V8 Git Publisher
   |- exact freshness preflight
   |- one local commit
   |- non-force branch push
   |- open/reuse one PR
   v
human review / merge
   X
no implicit Task completion / cleanup authority
```

## Closed gaps

1. A successful V7 record is no longer manually translated into Git publication; V8 can publish it under explicit operator intent.
2. Validation evidence is re-bound to the current workspace immediately before the first mutation.
3. Git commit/push authority is constrained to the active allocation repository/worktree/branch.
4. Shell interpretation and force push are excluded.
5. Publication persists phase evidence after irreversible steps and supports fail-closed resume.
6. Existing open PR detection prevents automatic duplicate PR creation.
7. CLI routing is part of the standard Engineering Graph local entrypoint.
8. V8 remains unable to approve, merge, auto-merge, complete Tasks, release leases, remove worktrees or mutate Neo4j.

## Candidate evidence

Implementation candidate `1dbf33e58a3f3f7d7166fb0cb806d48321be8430` passed:

- Spec Kit #397
- Engineering Graph #339
- Product CI #743

All three completed successfully on that exact implementation SHA. Product CI included typecheck, tests, build, Storybook/accessibility and Playwright E2E. Engineering Graph included the V1–V7 regression surface plus the V8 publisher tests.

## Freeze rule

**The commit containing this `convergence.md` file is the V8 freeze candidate.**

PR #24 may move from Draft to Ready for Review only when Spec Kit, Engineering Graph and Product CI all complete successfully on that exact commit SHA, with no subsequent content commit.

If any gate fails, the SHA is not frozen: fix the failure, create a new HEAD, and require all three gates again.

## Review and merge boundary

V8 can create the branch commit, push it and open/reuse a pull request. It cannot review or merge that pull request. PR #24 itself remains subject to the same human merge boundary.

After a V8-created PR is merged, canonical Task completion, lease release and worktree cleanup remain separate lifecycle decisions. Any automation of those actions requires a new numbered Spec Kit feature and an explicit authority decision; V8 must not silently grow into that role.
