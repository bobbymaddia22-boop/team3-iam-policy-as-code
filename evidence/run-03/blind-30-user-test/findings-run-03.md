# Run 03: Blind 30-user test (automated check and manual audit)

| | |
|---|---|
| **Control tested** | MFA is enabled for every IAM user who has a console password |
| **Environment** | Bobby Maddia's own standard AWS account (not the team sandbox; account ID masked) |
| **Population** | 30 synthetic users, t10 to t39, built by script: 10 COMPLIANT, 10 NON_COMPLIANT, 10 NOT_APPLICABLE in a shuffled order. The label of each user was written to the answer key before the user was built. |
| **Blind test?** | Partly. The script hid the per-user labels, and the auditor did not open the key or see the checker output before the audit was saved. The auditor is the same person who ran the build, so this is not an independent audit. No independent auditor is included in this run. |
| **Automated method** | Read-only boto3 collector and OPA rule (`automation/mfa_checker/`), run by Bobby Maddia. Commit: [confirm commit hash] |
| **Tool versions** | Python 3.13.17, OPA 1.22.2, boto3 [confirm version] |
| **Run identity** | Read-only scanner identity (`scanner-ro`, 3 IAM actions). Users were built with an administrator identity. |
| **Data source** | Live IAM API calls (no cached credential report) |
| **Manual method** | One auditor (Bobby Maddia), reading the IAM console Users list (MFA, Password age and Console access columns). Start 19:22:00, end 19:38:00 local time. |
| **Run date and time (UTC)** | Built 2026-11-12 02:24:16. Checker run 2026-11-13 01:38:28. |

## 1. Labeled population

Yes. 30 users were built (count confirmed: 30 users matching t10 to t39). The answer key (`answer-key.csv`) was created by the build script. Its SHA-256 was recorded right after the build and checked again before scoring; they match (`build-key-hash.txt`).

## 2. Automated results

| Measure | Value |
|---------|-------|
| Users scanned | 42 (the 30 test users plus 12 existing users) |
| Flagged noncompliant | 14 (10 of the test users, plus t2, t4, t7 and t8 from earlier runs) |
| Compliant | 12 |
| Not applicable | 16 |
| True positives / false positives | 10 / 0 (the 30 scored users) |
| False negatives / true negatives | 0 / 20 (the 30 scored users) |
| Known noncompliant control users flagged | 4 of 4 (t2, t4, t7, t8) |
| Run time (seconds) | 4.3647 |

Raw output: `checker-report.csv`, `screenshots/44-bulk-checker-run.PNG`

## 3. Manual audit results

| Measure | Value |
|---------|-------|
| Users audited | 30 |
| Flagged noncompliant | 10 |
| True positives / false positives | 10 / 0 |
| False negatives / true negatives | 0 / 20 |
| Total time (minutes) | 16 |

Raw record: `Audit_Bobby.xlsx` (unmodified). This run uses the auditor's spreadsheet instead of `manual-audit.csv`.

## 4. Disagreements

Scored by the column headers as written, the automated check, the manual audit and the answer key all agree for all 30 users (`scoring-blind-by-header/`).

One discrepancy in the audit file itself: in `Audit_Bobby.xlsx` the headers of columns B and C are swapped compared with the template (B is labeled `mfa`, C is labeled `console_password`), but the file's automatic status column (D) still assumed the template order. As a result, column D shows NOT_APPLICABLE for ten users that the key labels NON_COMPLIANT (t10, t14, t15, t16, t17, t26, t30, t32, t34, t35). The answers were entered under the headers as labeled and are correct, so this is a recording-layout error, not a judgement error. Fix: the scoring script reads the columns by header name, and the audit template should lock its header cells. The file is kept unmodified.

## Limits of this run

- One auditor, who is also the tester, and one run on 30 users. The timing comparison (4.4 seconds against 16 minutes) comes from one run each.
- The manual audit read the IAM console list, which is quicker than some audit methods, so the time is not comparable with Run 01.
- The check and the manual audit both depend on the same IAM data. Agreement shows consistency with the key, not that the key's rules are the right policy.
- The audit sheet showed how easily a manual record can go wrong (see section 4).
- Configuration only. This run does not test whether AWS blocks a sign-in or API call without MFA.
- The screenshot of the manual audit (43) shows users t10 to t37; t38 and t39 were read in the same list but are not visible in the image.

## Evidence files

| File | SHA-256 |
|------|---------|
| `answer-key.csv` | 620A372757073D3B8E4B5DA472FB210E8766CD1BF4ABCCB4970528934551D53B |
| `build-key-hash.txt` | 90D24816759029CDA1A7487025FBC4D72E98F4A851C30F2D5E65E35A288F9310 |
| `build-time.txt` | C424F250D5520CC5631A2F0D9F4360CAD6C04876870360F27B4AA37A85F9640A |
| `checker-report.csv` | 560DDD30B234CF4C66646478A7B79204477FC063CC1D6995B1556E6D0D11EDA8 |
| `checker-run-time.txt` | 7F1A439E49288B72AAACC1F75E30FBB6100D8F9ED1C923B6D448D1B17A74DE8E |
| `Audit_Bobby.xlsx` | 5ABA141D4F7880833A411981F6E1D4CBD5FB434183F72C88603D7A6EFC99C2FB |
| `scoring-blind-by-header/scoring-blind-results.md` | F0DAC5DD9A863619BB1369AA3ACBC6F27B4AF82D53004049036E35E498A453B2 |
| `scoring-blind-by-header/scoring-blind-results.json` | 06FCFEA61EEDE8CDC20994EEE47203F06D7A4CC08673A9C8C564ADCC1699878A |

Hashes for the README and screenshots are in `SHA256SUMS.txt`.
