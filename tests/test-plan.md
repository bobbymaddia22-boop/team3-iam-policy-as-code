# Test Plan: MFA Enforcement (AWS IAM)

**Version:** 0.1 (draft)
**Author:** [Your Name], Testing and Validation Lead
**Last updated:** [YYYY-MM-DD]
**Status:** Draft / In review / Approved

## 1. Control objective

Multi-factor authentication is required for IAM users who sign in to the AWS
Management Console and for sensitive API actions, and the root user is protected by MFA.

## 2. Baseline requirements

List the requirements this control is tested against. Verify the exact control
IDs against the version of each document your team is using.

| Ref | Source | Requirement (summary) |
|-----|--------|-----------------------|
| R1 | [CIS AWS Foundations Benchmark, control ID] | MFA enabled for the root user |
| R2 | [CIS AWS Foundations Benchmark, control ID] | MFA enabled for all IAM users with a console password |
| R3 | NIST SP 800-63B | Multi-factor authenticators for higher assurance levels |
| R4 | [Team requirement or other source] | [Summary] |

## 3. Scope

**In scope**
- IAM users with console access in the lab account
- A policy that denies sensitive actions unless MFA is present
- Root user MFA status
- IAM credential report data

**Out of scope**
- [Identity federation / SSO, unless the team adds it]
- [Production accounts or any real user data]

## 4. Test environment

| Item | Value |
|------|-------|
| AWS account | Lab account, ID shown as `111122223333` |
| Region | [e.g., us-east-1] |
| Test users | `test-user-mfa`, `test-user-nomfa` (placeholders) |
| Policy under test | [Name and link to the file in `/iam-config`] |
| Tools | AWS Console, AWS CLI, [boto3 script, if used] |
| MFA type | [Virtual authenticator app / hardware key] |

## 5. Assumptions and prerequisites

- The lab account is isolated from any real workloads.
- Test users and the policy under test exist before testing begins.
- Testers have a method for generating MFA codes for the test user.
- [Add more as needed]

## 6. Approach

Each test case is run manually first, with evidence captured. Where possible,
the same check is later repeated with a script so results are reproducible.

## 7. Pass/fail criteria

- **Pass:** The actual result matches the expected result and evidence is attached.
- **Fail:** The actual result differs from the expected result. Record the difference.
- **Blocked:** The test could not be run. Record the reason.
- The control is considered **validated** when all in-scope test cases pass.

## 8. Roles

| Person | Role |
|--------|------|
| [Name] | Testing and Validation Lead |
| [Name] | [Role] |

## 9. Risks and notes

- Note any limits of the lab environment that could affect results.
- Note anything about how the policy condition behaves for long-term access
  keys versus temporary session credentials, once the team has tested it.
