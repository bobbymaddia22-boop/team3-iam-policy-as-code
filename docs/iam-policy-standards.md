# IAM Identity Policy Standards

## Purpose
Define security requirements for IAM identity policies
managed in this repository.

## IAM-001: Valid policy syntax
All policy files must contain valid JSON and follow
the AWS IAM policy grammar.

## IAM-002: Least privilege
Grant only the actions and resources required by the
intended user, role, or workload.

## IAM-003: Wildcard actions
Action: "*" is prohibited by default. Exceptions require
documented justification and review.

## IAM-004: Resource scoping
Use specific resource ARNs where supported.
Resource: "*" must be reviewed for necessity.

## IAM-005: Review and traceability
Policy changes must be reviewed through pull requests.

## IAM-006: Automated validation
Policy changes must pass the repository's required checks.

## Exceptions
Document the rule, reason, owner, approval, and review date
for every approved exception.

## Scope
These standards initially cover IAM identity policies.
Resource policies and Service Control Policies are outside
the initial scanning scope.

## Limitations
Passing automated checks does not guarantee that a policy
is secure or implements least privilege.