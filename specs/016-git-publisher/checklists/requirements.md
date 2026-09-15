# Requirements Checklist: Git Publisher V8

- [x] Publication authority is explicitly separate from V7 validation authority.
- [x] Fresh passed V7 evidence is required before any Git mutation.
- [x] Workspace drift fails closed before commit.
- [x] Commit/push/PR commands are argv-based with no shell.
- [x] Push policy explicitly forbids force.
- [x] Remote repository identity is checked.
- [x] Partial publication has a durable recovery contract.
- [x] Resume cannot duplicate the validated commit.
- [x] PR creation does not imply approval/merge.
- [x] Task state, lease lifecycle, worktree cleanup and Neo4j remain outside V8 authority.
- [x] Credentials are environment-only.
- [x] Required final CI convergence is defined on one exact HEAD.
