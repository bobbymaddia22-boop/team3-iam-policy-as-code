# 0002: Separate data collection from policy evaluation

**Date:** [YYYY-MM-DD]
**Status:** Proposed (add the finding, then change to Accepted)
**Decided by:** [Carlton and team members who agreed]

## Context
The automated check (`automation/mfa_checker/`) has two parts: `collect_iam_state.py` gathers IAM data, and `policy/mfa.rego` evaluates it with OPA.

## Finding
[Venika: add one specific, cited research finding that supports this design, for example a source describing policy-as-code or separating evidence collection from evaluation. State what the source says, not just its title. Delete this decision if no finding supports it.]

## Decision
The collector only reads and records data. The Rego policy only evaluates a saved snapshot. Neither part does the other's job.

## Consequences
- The policy can be tested without AWS (`policy/mfa_test.rego`).
- The collector can be limited to read-only permissions.
- The snapshot is the traceable input for each run, and it is not committed because it contains an unmasked account ID.
