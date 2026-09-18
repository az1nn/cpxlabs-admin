# Quickstart: Remote Branch Cleanup V11

## Goal

Validate that V11 can identify and safely remove exactly one completed remote feature branch without widening authority.

## Prerequisites

- Python >=3.13 Engineering Graph environment installed.
- Git available.
- A test repository with a disposable bare remote.
- Terminal V8 publication evidence and matching finalized V9 receipt for the test identity.

## Scenario 1 — Read-only ready assessment

1. Create a disposable remote branch at the exact publication commit.
2. Run:

```bash
graph-engineering remote-cleanup-status --publication <ID> --json
```

3. Verify:
   - `ready=true`;
   - expected and observed SHAs match;
   - no local/remote ref changed;
   - no receipt was written by status.

## Scenario 2 — Guarded deletion

Run:

```bash
graph-engineering remote-cleanup-finalize \
  --publication <ID> \
  --delete-remote-branch \
  --json
```

Verify:

- only the exact target remote head is absent afterward;
- sibling heads and tags are unchanged;
- a derived `deleted` receipt exists;
- rerunning finalize performs no second destructive operation.

## Scenario 3 — Race protection

1. Produce a ready assessment for expected SHA A.
2. Move the remote branch to SHA B before finalize.
3. Run finalize.
4. Verify:
   - deletion is rejected;
   - branch remains at SHA B;
   - result surfaces expected A vs observed/current B;
   - no unconditional fallback occurs.

## Scenario 4 — Already absent

Delete the target branch externally before V11 finalize, then run status/finalize.

Verify:

- outcome is `already_absent`;
- no delete command is necessary;
- result remains idempotent.

## Scenario 5 — Protected identities

Exercise a target identity that equals base/default branch or retains active local ownership.

Verify V11 blocks before issuing any remote mutation.

## Regression

Run the complete Engineering Graph suite, then require repository Spec Kit, Engineering Graph and Product CI workflows to succeed on the same final freeze HEAD.
