# Convergence: Agent Validator V7

## Outcome

V7 converges the execution-to-validation gap without expanding into canonical completion or Git publication authority.

The final design is intentionally layered:

```text
V3 allocation / frozen validation commands
              |
              v
V5 successful process evidence
              |
       optional V6 ownership
              |
              v
V7 stable-workspace validation evidence
              |
              X  no implicit authority escalation
       future publication spec/ADR
```

## Closed gaps

1. Process exit code 0 is no longer the only available post-execution signal; V7 can execute deterministic allocation-specific validation gates.
2. Callers cannot redefine validation commands at execution time.
3. Shell interpretation is not used.
4. V5/V6 evidence is tied to the exact active allocation before validation starts.
5. Validation evidence is bound to a stable publishable workspace fingerprint.
6. Results/logs have a versioned disposable persistence contract.
7. Validation remains distinct from Task completion, lease lifecycle and provider/Git publication.

## Candidate evidence

The implementation candidate `40b326795126ab30696c9633157b61f3a3d01fde` passed Spec Kit #387, Engineering Graph #320 and Product CI #722. That candidate established implementation correctness before the final documentation/convergence alignment.

## Freeze rule

The commit containing this convergence file is the V7 freeze candidate. It is eligible to move PR #23 from draft to Ready for Review only if **Spec Kit, Engineering Graph and Product CI all complete successfully on that exact commit SHA**, with no subsequent content commit.

If any gate fails, the candidate is not frozen: fix the failure, update evidence if the design changes, and require all three gates again on the new exact HEAD.

## Publication boundary

PR #23 itself is the human review boundary for V7. This feature does not merge itself and does not implement commit/push/PR/merge automation for supervised task work. A future publication layer requires a new numbered Spec Kit feature and ADR.
