# Security Analysis

Assets, actors, threats, controls, residual risks, and safe-use limits for the MFA
configuration check. It covers this project's tool and evidence, not the security of an AWS account in general.

## Assets

| Asset | Why it matters |
|-------|----------------|
| Lab AWS account (the sandbox) | The only account the tool is meant to touch. |
| Scanner identity's credentials | Read-only, but a leaked key still lets someone list the account's users and MFA state. |
| `snapshot.json` | Holds the full account ID and MFA device ARNs. |
| Answer key and its hash (blind test) | If the key is seen early, the blind test is not blind. |
| Evidence (reports, hash lists, screenshots) | The project's claims rest on it. It must be accurate and must not leak account details. |
| The public repository and its history | Anyone can read every file and every past commit. |

## Actors

| Actor | Relationship |
|-------|--------------|
| Operator (team member) | Runs the check and commits evidence. |
| Manual auditor | Reads the IAM console to produce the comparison baseline. |
| Instructor and reviewers | Read the repository and the video. |
| Public reader | Can see everything committed. Not trusted with credentials or account details. |
| An attacker who obtains the scanner credentials | Could read IAM state in the lab account. Cannot change it with the scanner policy. |
| AWS | Provides the data. Its credential report can be up to four hours old. |

## Threats, controls, and results

| Threat | Control in the project | Evidence |
|--------|------------------------|----------|
| The tool runs against the wrong account | `--approved-account-id` is checked first; a mismatch exits with code 2 before any IAM call | Live run and unit tests, `evidence/support/scanner-identity-and-negative-tests/` |
| The tool changes something in AWS | Scanner identity has `ListUsers`, `ListMFADevices`, `GetLoginProfile` only; a test fails if any other call is made | `scanner-iam-policy.json`, `automation/mfa_checker/tests/test_pipeline.py` |
| A failed or partial scan gives a false "all clear" | Any AWS error exits with code 3 and writes no report | Live run under a no-permission identity |
| Account ID leaks through reports | `--mask-account-id`; `snapshot.json` is in `.gitignore` | `.gitignore`, README rules |
| Account ID leaks through screenshots or error text | A person checks every screenshot at full size. Error text still prints the full ID, so it is cropped or masked before commit | Documented in `evidence/README.md` |
| Credentials or keys are committed | Rules in the README and working agreement; the history was scanned for keys and 12-digit account IDs before publication | Scan of the full history |
| Evidence is changed after the fact | SHA-256 hash lists for the runs that have them; the blind-test answer key is hash-locked at build time and checked before scoring | `SHA256SUMS.txt` files, `build-key-hash.txt` |
| The manual audit is recorded wrongly | The scoring script reads audit columns by header name; the template locks its header cells | Run 03 findings (swapped headers caught and handled) |
| Dependencies change under the project | Versions are recorded in `THIRD_PARTY.md` and the run findings | `THIRD_PARTY.md` |
| Changes reach `main` without review | Branch and pull-request workflow | Pull request history |

## Residual risks

- **Point-in-time.** A result is true only at the moment of the run. A user changed afterward is not reflected.
- **Small, synthetic populations.** Accuracy figures are descriptive, not an estimate for real accounts.
- **One method of reading devices.** How passkeys and security keys appear in the device list was not verified until the sandbox run that includes one.
- **Partial permission denial.** A scan that is denied on some calls but not others, has not been tested in a live run.
- **Registered is not enforced.** The check shows a device is registered. It does not show AWS blocks a sign-in that lacks MFA.
- **Local copies.** The snapshot holds the full account ID on the operator's machine until it is deleted.
- **Single auditor.** In the blind test, the tester built the users and did the only audit.
- **Public history.** Anything ever committed stays readable. A credential in an old file is fixed by deleting the credential, not by removing the file.

## Safe-use limits

- Use it only in an AWS account the team owns and has approved. Never against an account you do not control.
- Use a read-only identity. Do not run it with administrator or write-capable credentials.
- Never put real credentials, account IDs, user names, or unmasked screenshots in the repository.
- Do not use the result as a compliance attestation or as evidence that an account meets CIS or NIST requirements.
- Treat a COMPLIANT result as "a device is registered at the time of the run", nothing more.
