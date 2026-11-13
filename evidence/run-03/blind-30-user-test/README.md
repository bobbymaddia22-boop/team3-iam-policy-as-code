# Blind 30-user test 

Compares the automated MFA check with a manual audit on 30 synthetic users (t10 to t39) whose expected labels were hidden from the tester until scoring.

## Method
- A script built t10 to t39 with a shuffled mix of 10 COMPLIANT, 10 NON_COMPLIANT and 10 NOT_APPLICABLE users. The labels were written to a file before each user was built, and the file was not opened until scoring.
- Build time (UTC): 2026-11-12T02:24:16.6551934Z
- Key file SHA-256, recorded right after the build and checked again before scoring (match): 620A372757073D3B8E4B5DA472FB210E8766CD1BF4ABCCB4970528934551D53B
- Manual audit: one auditor (the tester), reading the IAM console Users list. Start 19:22:00, end 19:38:00 local time (16 minutes). The auditor did not see the checker output or the key.
- Automated check: run under the read-only scanner identity (scanner-ro) at 2026-11-13T01:38:28.6768506Z (UTC). It scanned 42 users (the 30 test users plus 12 existing), found 14 noncompliant, and took 4.3647 seconds.

## Results (positive class NON_COMPLIANT)
| Method | Correct | TP | FP | FN | TN | Time |
|---|---|---|---|---|---|---|
| Automated check | 30/30 | 10 | 0 | 0 | 20 | 4.4 s |
| Manual audit | 30/30 | 10 | 0 | 0 | 20 | 16 min |

## Note on the audit sheet
In the submitted audit file (Audit_Bobby.xlsx, SHA-256 5ABA141D4F7880833A411981F6E1D4CBD5FB434183F72C88603D7A6EFC99C2FB) the headers of columns B and C are swapped compared with the template: B is labeled mfa and C is labeled console_password. The file's automatic status column (D) still assumed the template order, so it shows NOT_APPLICABLE for the 10 users with a console password and no MFA. The answers themselves were entered under the headers as labeled and are correct. The scoring script reads the columns by header name, so the results above score the answers as recorded. The file is kept unmodified. This is a recording-layout error, not a judgement error, and it shows how easily a manual audit sheet can go wrong.


## Files
answer-key.csv, build-time.txt, build-key-hash.txt, checker-report.csv, checker-run-time.txt, Audit_Bobby.xlsx, scoring-blind-by-header/, screenshots/, SHA256SUMS.txt.


