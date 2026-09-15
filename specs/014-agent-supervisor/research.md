# Research: Agent Supervisor V6

## Decision 1 — Supervisor state remains local derived state

The supervisor records scheduling policy and observations that cannot be deterministically rebuilt from canonical Git alone (for example which local run ids belonged to one orchestration attempt). This state belongs under `.execution/` and must remain disposable rather than projected into Neo4j.

## Decision 2 — Tick-based coordination instead of a resident daemon

A deterministic `supervisor-tick` command is easier to inspect, test and recover than a permanently resident scheduler. Each invocation reconciles V5 evidence, launches only currently eligible work and persists the resulting derived state. A future daemon can call the same tick primitive without changing semantics.

## Decision 3 — Retry only execution failures/orphans

`failed` and `orphaned` are execution observations that may be retried within an explicit bound. `stopped` represents an explicit lifecycle intervention and is therefore never retried automatically. `succeeded` remains process success only.

## Decision 4 — No automatic validation/publication in V6

Validation commands are already carried by V3 allocations, but running them and interpreting them as completion evidence is a separate policy surface. Commit/push/PR automation has an even stronger provenance/review boundary. Both remain deferred.

## Decision 5 — Stop delegates to V5

V5 already owns PID/fingerprint verification and process-group signaling. V6 must not duplicate process-safety logic. It verifies run ownership by `runId`, then delegates stop to V5.
