# Run 02: Edge cases (t6 to t8) added to the labeled population

| | |
|---|---|
| **Control tested** | MFA is enabled for every IAM user who has a console password |
| **Environment** | Bobby Maddia's own standard AWS account (not the team sandbox; account ID masked). Same configuration as the team sandbox, rebuilt by script. |
| **Population** | Eight synthetic users. t1 to t5 are the Run 01 cases, rebuilt by script. t6 to t8 are new edge cases, built by script. The intended state of every user was written to the answer key before the user was built. Built by Bobby Maddia. |
| **Blind test?** | No. The tester built the users and knew their configurations. |
| **Automated method** | Read-only boto3 collector and OPA rule (`automation/mfa_checker/`), run by Bobby Maddia. Commit: [confirm commit hash] |
| **Tool versions** | Python 3.13.17, OPA 1.22.2, boto3 [confirm version] |
| **Run identity** | Read-only scanner identity (`scanner-ro`, 3 IAM actions: ListUsers, ListMFADevices, GetLoginProfile) |
| **Data source** | Live IAM API calls (no cached credential report) |
| **Manual method** | None in this run. No manual audit was done. |
| **Run date and time (UTC)** | 2026-11-08 [time not recorded] |

## 1. Labeled population

Yes. All eight users were built and match the answer key in `edge-cases-t6-t8/labeled-population.csv`.

| User | Setup | Expected |
|------|-------|----------|
| t1 | Console password, one MFA device | COMPLIANT |
| t2 | Console password, no MFA | NON_COMPLIANT |
| t3 | No console password | NOT_APPLICABLE |
| t4 | MFA added, then removed | NON_COMPLIANT |
| t5 | Console password, two MFA devices | COMPLIANT |
| t6 | Console password and MFA device set, then the password removed | NOT_APPLICABLE |
| t7 | Console password, must be reset at next sign-in, never used, no MFA | NON_COMPLIANT |
| t8.test+mfa,Case=A@team3 | Special characters in the name, console password, no MFA | NON_COMPLIANT |

## 2. Automated results

| Measure | Value |
|---------|-------|
| Users scanned | 12 (the 8 test users plus 4 non-test identities, all NOT_APPLICABLE). `report.csv` lists only the 8 test users so every user is in the answer key. |
| Flagged noncompliant | 4 (t2, t4, t7, t8.test+mfa,Case=A@team3) |
| Compliant | 2 (t1, t5) |
| Not applicable | 2 of the 8 test users (t3, t6) |
| True positives / false positives | 4 / 0 |
| False negatives / true negatives | 0 / 4 |
| Known noncompliant control users flagged | 4 of 4 (t2, t4, t7, t8) |
| Run time (seconds) | 1.3377 (screenshot 30) |

Raw output: `edge-cases-t6-t8/report.csv`, `edge-cases-t6-t8/screenshots/30-edge-case-run.png`

## 3. Manual audit results

Not performed in this run.

## 4. Disagreements

None. All eight users match the answer key. Notes on what the edge cases show:
- t6: the rule depends on the console password, not on whether an MFA device exists.
- t7: a user with a console password who has never signed in is still NON_COMPLIANT. This assumes no grace period for new users. The team should record this decision.
- t8: a comma and other special characters in a username stay inside one quoted CSV column and the user is not skipped.

## Limits of this run

- Eight synthetic users, and not blind. One misclassified user would change a rate by a large step, so the rates are descriptive, not an estimate of real-world accuracy.
- Run in a different account and under a different identity (read-only scanner) than Run 01 (team sandbox, root user), so the two runs are not a like-for-like comparison.
- Live IAM API data only. The check was not compared with the AWS credential report in this run (see `support/credential-report-cross-check/`).
- Configuration only. The check tests registered MFA devices, not whether AWS blocks a sign-in or API call without MFA.
- The build scripts are not in the repository yet. [confirm path once added]

## Evidence files

| File | SHA-256 |
|------|---------|
| `edge-cases-t6-t8/labeled-population.csv` | D9DC4BB05BDB049DFFE0AA4BA29BDC7F9389B7F22A13327F2EEA491C6D523CF0 |
| `edge-cases-t6-t8/report.csv` | E64F6572093D815DE81791385F3D05B7875DE58240E7F8EC5DFC54A51742F38B |
| `edge-cases-t6-t8/scoring-results.md` | 152E76717D7190D71BFE8B4DA78B168D280E6E9DD036CD0FCFD4265679E08C42 |
| `edge-cases-t6-t8/scoring-results.json` | 23B3C08450B7822FF344F04D579B63DD880D5BE763C2987D83B050C6FFDDE79C |
| `edge-cases-t6-t8/screenshots/30-edge-case-run.png` | 14CA1CA4C5AB4E0A5E752C2EDD4E77AE84DE31DD0E9580EA01C93B891B46F1DF |
