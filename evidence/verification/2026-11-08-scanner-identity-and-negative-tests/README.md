# Scanner-identity run and negative tests

- Environment: Bobby Maddia's own practice AWS account (standard account, not the team sandbox; account ID not recorded here).
- Population: t1 to t5, the same users as ../2026-11-07-practice-account-run/ (answer key: labeled-population.csv in that folder).
- Tools: Python 3.13.17, OPA 1.22.2.


## Results

| Test | Identity | Result | Exit code | Screenshot |
|---|---|---|---|---|
| Checker (run_check.py) | scanner-readonly (3-action policy) | 5 of 5 exact matches; TP=2 (t2, t4), FP=0, FN=0, TN=3; about 1.0 s | 0 | 20 |
| Wrong account (fake approved ID) | scanner-readonly | Refused before any IAM call | 2 | 21 |
| Validation script (check_mfa_status.py), denied permission | scanner-readonly | AccessDenied, clean error | 2 | 22 |
| Validation script (check_mfa_status.py) | validation-readonly (6-action policy) | t2 and t4 FAIL; root MFA PASS | 1 | 23 |
| Checker, AWS error | no-permission user | AccessDenied on iam:ListUsers; no report written | 3 | 24 |

report.csv is the checker output (bobby-admin, scanner-readonly, validation-readonly) removed so every user is in the answer key.

## Notes

- This run uses the read-only scanner identity, so it closes the "ran under an admin identity" caveat from the 2026-11-07 run.
- Exit code 1 from check_mfa_status.py means at least one FAIL, which is expected (t2 and t4).
- Finding: --mask-account-id masks the report files only. When AWS returns an error, the checker prints AWS's error text, which contains the full account ID. In screenshot 24 the ID was masked by a display filter in the command (-replace ... XXXX); the checker itself did not mask it.
- Screenshot 21 uses a deliberately wrong account ID (123456789012).
