# Test Plan: IAM Console-User MFA Check

**Version:** 0.2 (draft)
**Author:** Bobby Maddia, Testing and Validation Lead
**Last updated:** 2026-11-1
**Status:** Draft, in review

## 1. Control under test

Every IAM user who has a console password must have at least one MFA device registered.

This plan tests whether the check **detects that configuration correctly**. It does not test whether AWS blocks a sign-in or API call that lacks MFA. That is a separate question and is listed under "Later work" in section 3.

## 2. Baseline requirements

Confirm each control ID against the document version the team actually cites before this plan is approved.

| Ref | Source | Requirement (summary) | Version / control ID |
|-----|--------|-----------------------|----------------------|
| R1 | CIS AWS Foundations Benchmark | MFA enabled for all IAM users that have a console password | [confirm version and control ID from the benchmark PDF] |
| R2 | CIS AWS Foundations Benchmark | MFA enabled for the root user (reported separately, not scored here) | [confirm version and control ID] |
| R3 | NIST SP 800-63B-4 | Multi-factor authenticators for higher assurance levels (background only) | [confirm section] |

## 3. Scope

**In scope**
- IAM users in the sandbox account, classified by console password and registered MFA devices.
- Comparison of the automated check against a manual audit on the same five users.
- Root MFA status, **reported separately** and never counted in the user-control score.

**Later work (not part of this run)**
- Deny-without-MFA policy and the IAM policy simulator cases (formerly MFA-03, MFA-04, MFA-08).
- Live sign-in or API enforcement testing.
- Comparison with the AWS Config managed rules.
- Rerun under the read-only scanner identity.

**Out of scope**
- Identity federation / SSO.
- Production accounts or any real user data.

## 4. Test population

Five synthetic users, created and labeled before either method runs. Ground truth is recorded in `evidence/run-01/labeled-population.csv`.

| ID | Console password | MFA devices | Configuration | Expected status |
|----|------------------|-------------|---------------|-----------------|
| t1 | Yes | 1 | Console password and one MFA device | COMPLIANT |
| t2 | Yes | 0 | Console password and no MFA device | NON_COMPLIANT |
| t3 | No | 0 | No console password (access key only) | NOT_APPLICABLE |
| t4 | Yes | 0 | Console password; MFA device added then removed | NON_COMPLIANT |
| t5 | Yes | 2 | Console password and two MFA devices | COMPLIANT |

## 5. Test environment

| Item | Value |
|------|-------|
| AWS account | Sandbox account, ID shown as `111122223333` in the repository |
| Region | [confirm] |
| Identity used for the run | [confirm with Steve: root, console identity, or scanner role] |
| Automated method | OPA/Rego pipeline in `automation/mfa_checker/` (Carlton) |
| Cross-check | Python scripts in `scripts/` (Bobby) |
| Manual method | [confirm: console or credential report], following `tests/manual-audit-procedure.md` |

## 6. Approach: how the comparison is kept fair

1. **Same population.** Both methods audit the same five users in the same account state. Nobody changes a user between runs.
2. **Same evidence source for every user.** The manual procedure names its source. If the manual auditor reads the credential report and the automated check reads the same report, record that, because the comparison then measures reading effort, not independent data.
3. **Blind to ground truth.** The auditor and the person running the automated check do not see `labeled-population.csv` until both result files are saved. Someone else (the person who built the population) holds the labels.
4. **Results saved before scoring.** Each method writes its results file and records its SHA-256 hash before anyone compares them with the labels.
5. **Timing boundaries defined** in `tests/manual-audit-procedure.md` and in section 7 below. Time is measured with a stopwatch per method, not estimated.

## 7. Metrics

- **Positive class:** NON_COMPLIANT.
- **Confusion matrix** per method against the labeled expected status.
- **Precision, recall and false-positive rate**, with the counts shown. With five users, one miss moves a rate by a large step, so treat the rates as descriptive only.
- **Time:**
  - *Automated:* from starting the command to the results file being written.
  - *Manual:* from receiving the audit instructions to saving the completed results file.
  - Setup, labeling and report writing are excluded from both, and the exclusion is stated in the findings.
- **Agreement:** list every user where the two methods disagree and explain why.

## 8. Pass/fail criteria

- **Method result for a user:** matches the expected status = correct; otherwise incorrect. Record the difference.
- **Run valid:** both result files exist, hashes are recorded, and the account ID check passed.
- **Blocked:** the run could not be completed. Record the reason.
- The control check is considered **supported by this run** if it classifies all five users correctly. A single run on five synthetic users cannot show more than that.

## 9. Safety requirements

| Ref | Requirement | Test or evidence |
|-----|-------------|------------------|
| SR2 | Checks are read-only | scanner-iam-policy.json|
| SR3 | Refuse to run against the wrong account | [Planned] |
| SR4 | Results are traceable to a run | [list evidence, for example hashes in `findings.md`] |


## 10. Roles

| Person | Role |
|--------|------|
| Bobby Maddia | Testing and Validation Lead |
| Carlton | Automation (OPA/Rego) |
| Steve | AWS environment and live run |
| Venika | Research and Risk Lead |
| Dana DiLeo | Head of Documentation and write-ups |

