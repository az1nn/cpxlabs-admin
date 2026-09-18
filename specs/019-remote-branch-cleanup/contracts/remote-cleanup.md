# Contract: Remote Branch Cleanup V11

## Commands

### Read-only status

```bash
graph-engineering remote-cleanup-status \
  --publication <PUBLICATION_ID> \
  --json
```

Human-readable output is the default when `--json` is omitted.

Contract:

- no remote/local mutation;
- derives branch and expected SHA from publication evidence;
- requires matching finalized V9 evidence;
- reports exact remote state, blockers and one next action.

### Explicit finalize

```bash
graph-engineering remote-cleanup-finalize \
  --publication <PUBLICATION_ID> \
  --delete-remote-branch \
  --json
```

Contract:

- `--delete-remote-branch` is mandatory explicit intent;
- command re-assesses fresh state before mutation;
- target branch is not accepted as an arbitrary argument;
- guarded deletion requires the remote head still equal the publication commit SHA;
- no unconditional-delete fallback is permitted.

## Status JSON shape

```json
{
  "assessmentVersion": "1",
  "repository": "owner/repo",
  "publicationId": "pub-...",
  "specId": "SPEC-...",
  "taskId": "SPEC-...:T...",
  "remote": "origin",
  "branch": "exec/...",
  "fullRef": "refs/heads/exec/...",
  "expectedSha": "40-hex",
  "observedSha": "40-hex-or-null",
  "remoteState": "present",
  "ready": true,
  "terminalWithoutMutation": false,
  "blockers": [],
  "nextAction": "delete_remote_branch"
}
```

Closed `remoteState` vocabulary:

- `present`
- `absent`
- `unavailable`
- `conflict`

Closed `nextAction` vocabulary:

- `delete_remote_branch`
- `finish_local_cleanup`
- `repair_evidence`
- `inspect_remote_policy`
- `retry_remote_inspection`
- `none`

## Receipt outcomes

- `deleted`
- `already_absent`
- `blocked`
- `failed`

A `deleted` receipt is valid only for the exact repository/remote/branch/expected-SHA identity recorded in that receipt.

## Process safety

Any Git command that consumes branch/ref identity is invoked as argv with `shell=False`.

The planned deletion primitive is an exact deletion refspec guarded by an expected old SHA, equivalent in semantics to:

```text
git push --porcelain --force-with-lease=refs/heads/<branch>:<expectedSha> origin :refs/heads/<branch>
```

This contract does not authorize a fallback to `git push --delete` or another unconditional mutation when the guarded operation fails.

## Lifecycle integration

If the existing lifecycle assessment vocabulary is extended, the change must be versioned. Existing V10 assessments remain interpretable, and remote cleanup remains a derived post-finalization tier rather than canonical Task state.
