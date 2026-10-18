# Run 01: Labeled Population, Automated Check vs. Manual Audit

| | |
|---|---|
| **Control tested** | MFA is enabled for every IAM user who has a console password (benchmark reference in `tests/test-plan.md`) |
| **Environment** | Team 3 Capstone Project sandbox account (dedicated, non-production; account ID masked). The automated check was run in AWS CloudShell. |
| **Population** | Five synthetic IAM users, t1 to t5, built by Steve Bilali (Environment Lead) |
| **Blind test?** | No. The auditor knew how each user was configured. |
| **Automated method** | Read-only boto3 collector and OPA rule (`automation/mfa_checker/`), developed by Carlton Ferdinand and run by Steve Bilali |
| **Tool versions** | Python 3.13, boto3 1.43.83, OPA 1.21.1 |
| **Run identity** | The root user, not the read-only scanner identity. |
| **Data source** | Live IAM API calls (no cached credential report) |
| **Manual method** | Manual audit of each user, performed by Bobby Maddia (Testing and Validation Lead). Evidence source: IAM console. |
| **Run date** | 2026-10-05 |


## Summary

In this run the automated check and the manual audit both matched the answer key for all five
users, with no disagreements. The automated check took about 0.56 seconds. The manual audit took
about 15 minutes.

The positive class is `NON_COMPLIANT`, meaning a user the control should flag.

| Measure | Automated check | Manual audit |
|---------|-----------------|--------------|
| Users scored | 5 | 5 |
| Matches the answer key | 5 of 5 | 5 of 5 |
| True positives (t2, t4) | 2 | 2 |
| False positives | 0 | 0 |
| False negatives | 0 | 0 |
| True negatives (t1, t3, t5) | 3 | 3 |
| Precision / recall / false-positive rate | 1.00 / 1.00 / 0.00 | 1.00 / 1.00 / 0.00 |
| Time, total | about 0.56 seconds | about 15 minutes |
| Time, per user | about 0.11 seconds | about 3 minutes |

The automated check was roughly 1,600 times faster (900 seconds divided by 0.56 seconds).

## 1. Labeled population

**Result: built, and every user matches its label.** Steve Bilali built the users and the
auditor confirmed which test case applies to each one before scoring. The answer key is in
`labeled-population.csv`.

| User | Console password | MFA devices | Expected status |
|------|------------------|-------------|-----------------|
| t1 | Yes | 1 | COMPLIANT |
| t2 | Yes | 0 | NON_COMPLIANT |
| t3 | No (access key only) | 0 | NOT_APPLICABLE |
| t4 | Yes | 0 (device added, then removed) | NON_COMPLIANT |
| t5 | Yes | 2 | COMPLIANT |

All MFA devices are virtual devices registered with Microsoft Authenticator.

t3 and t4 are the boundary cases. t3 checks that a user with no console password is excluded rather
than wrongly flagged. t4 checks that a user whose MFA device was removed is flagged, even though
the user once had one. t5 checks that more than one device is handled.

## 2. Automated results

| Measure | Value |
|---------|-------|
| Users scanned | 5 |
| Flagged noncompliant | 2 (t2, t4) |
| Compliant | 2 (t1, t5) |
| Not applicable | 1 (t3) |
| True positives / false positives | 2 / 0 |
| False negatives / true negatives | 0 / 3 |
| Known noncompliant control users flagged | Both (t2 and t4) |
| Run time | about 0.56 seconds (collect and evaluate) |

This was a single run on five users, made once, at one point in time.

Raw output files are in `automated/`, and screenshots are in `screenshots/`. See the README in
each folder for what to add.

## 3. Manual audit results

The auditor checked each user for a console password and an MFA device.

| Measure | Value |
|---------|-------|
| Users audited | 5 |
| Flagged noncompliant | 2 (t2, t4) |
| True positives / false positives | 2 / 0 |
| False negatives / true negatives | 0 / 3 |
| Time | about 3 minutes per user, about 15 minutes in total |

The per-user times in `manual-audit.csv` are the reported average, not individual stopwatch
readings. Replace them with exact times in a later run if the auditor records them.

## 4. Disagreements

**None.** The automated check, the manual audit, and the answer key agreed on all five users,
including both boundary cases (t3 and t4).

A disagreement is expected in a later comparison with the AWS Config managed rule
`iam-user-mfa-enabled`, which evaluates all IAM users rather than only users with a console
password, so it should treat t3 differently. That comparison has not been run yet. See Next tests.

## What this run does and does not show

**It shows** that on this population the automated check reproduces the answer key and is far
faster than a manual audit.

**Limits:**
- **Small population.** Five users with two positives is weak evidence of accuracy. A result of
  100% on five users does not predict 100% on five hundred.
- **Not a blind test.** The auditor knew how each user was configured, which can make the manual
  audit look better than it would on an unfamiliar account.
- **One timing run.** The 0.56 second figure comes from a single run. Repeat runs will give a mean
  and range.
- **The timings measure different things.** The script time covers collection and evaluation only.
  The manual time is a person working through the audit. Neither includes setup or reviewing the
  results.
- **Administrative identity.** The check made only read calls, but it ran under an administrative
  identity. It has not yet been run under the read-only scanner identity, so the read-only
  safeguard (SR2) is untested with limited permissions.
- **Virtual devices only.** Passkeys and security keys were not part of the population.
- **Manual evidence source.** The source the auditor used (console or credential report) must be
  recorded, because it can affect accuracy and time.
- **Point in time.** A user changed after the scan is not seen until the next scan.

## Next tests

The question this run leaves open is how the check scales and how it reacts to conditions it has
not seen. For each test below, record the same four items using `../run-template.md`.

- **Blind manual audit.** Someone who did not build or label the population audits it, with the
  answer key kept out of view until the audit is finished.
- **Read-only scanner identity.** Rerun the check as the scanner identity, and test that it refuses
  to run against the wrong account (SR2 and SR3).
- **AWS Config comparison.** Run `iam-user-mfa-enabled` (all users) and
  `mfa-enabled-for-iam-console-access` (users with a console password). Log any difference from the
  check, starting with t3. Observe how the second rule treats t3 rather than assuming it.
- **Enforcement tests.** The planned enforcement check, login event check, and IAM policy simulator
  test. These test whether MFA is required, not only whether a device is registered.
- **A larger population** of users.
- **Passkey or security-key (FIDO) devices.**
- **A user changed after the collector has run.**
- **A denied permission,** which should stop the run with no report rather than a clean-looking one.
- **Repeated runs,** to give a mean and range for the timing comparison.

## Evidence files

| File | Contents | SHA-256 |
|------|----------|---------|
| `labeled-population.csv` | Answer key for t1 to t5 | |
| `manual-audit.csv` | Manual verdicts and approximate times | |
| `automated/report.json` | Automated check output (add) | |
| `automated/report.csv` | Automated check output (add) | |
| `screenshots/` | Redacted console and terminal screenshots (add) | not applicable |

Compute each hash as described in `../README.md`.
