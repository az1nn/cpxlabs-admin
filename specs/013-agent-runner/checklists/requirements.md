# Requirements Checklist: Agent Runner V5

- [x] Scope is limited to process lifecycle over active V3 allocations.
- [x] Git/Spec Kit/code/tests remain canonical.
- [x] Runner state is derived/disposable.
- [x] Process exit is explicitly not Task completion.
- [x] Commit/push/PR/merge automation is out of scope.
- [x] Automatic lease release is out of scope.
- [x] Commands are argv-based and `shell=False`.
- [x] Worktree/cwd confinement is explicit.
- [x] PID reuse/process identity risk is addressed fail-closed.
- [x] stdout/stderr/result persistence is specified.
- [x] Secret environment values are excluded from persisted state.
- [x] Duplicate active task runs are rejected.
- [x] Product runtime isolation remains required.
- [x] CI uses harmless local fixtures only.
- [x] Final freeze requires Spec Kit + Engineering Graph + Product CI on the same HEAD.
