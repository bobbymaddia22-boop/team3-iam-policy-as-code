# Policies

Baseline requirements and machine-readable policies for the project.

- The OPA rule for MFA enforcement is in `automation/mfa_checker/policy/mfa.rego`. It is
  kept next to the collector so the check runs as delivered.
- Security requirements for IAM identity policies are in `docs/iam-policy-standards.md`.

Add additional baseline requirements here as the team takes on more controls.
