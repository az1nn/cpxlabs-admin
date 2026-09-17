# Continuation Prompt Template

Use this at the end of every material development update that leaves follow-up work possible.

```text
Continue CPXLabs Admin in `az1nn/cpxlabs-admin`.

Freshness first:
- verify target base: <base branch + current SHA>
- verify active branch: <branch>
- verify active PR: <PR number/url/state>
- verify expected HEAD: <SHA>
- verify active Spec Kit feature/task state: <SPEC / task scope>
- re-check automated gates and Human Async Gates before any mutation

Current state:
- completed: <concise outcomes>
- automated gates: <run IDs/status/freshness>
- Human Async Gates: <Gate IDs/status/freshness, or none>
- blockers/open items: <items>

Authority boundary:
<what the agent may do now and what still requires canonical/human evidence>

Next Action:
<one exact executable next action>

Treat Git-backed code/specs/ADRs/tests/history as authoritative. Derived handoffs, ContextPackages, lifecycle receipts, prior CI summaries and this prompt are non-authoritative if repository state has changed. Continue autonomously through safe steps, but do not cross pending human/merge/task/cleanup authority gates.
```

## Rules

- Regenerate after HEAD, PR, Spec Kit, CI, or Human Async Gate state changes.
- Never omit a required `PENDING` Human Async Gate.
- If the current feature is fully closed, set `Next Action` to verify the merged base and start the next numbered Spec Kit feature in a new branch/PR.
- Keep one exact Next Action; do not make the next session reconstruct priorities from a list.
