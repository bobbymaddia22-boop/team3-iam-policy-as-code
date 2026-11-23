# Test scripts

Scripts that build the synthetic test users, remove them, and score the blind test. They are
tools for the team's own lab account. Nothing here is part of the automated check itself
(`automation/mfa_checker/`).

## Scripts

| Script | What it does | Touches AWS |
|--------|--------------|-------------|
| `build_t1_t5.py` | Builds (or removes) the five labeled users t1 to t5 and writes their expected statuses to `labeled-population.csv` | Yes |
| `build_edge_cases.py` | Builds (or removes) the edge-case users t6, t7, and t8 and writes their expected statuses before each user is built | Yes |
| `build_bulk.py` | Builds the 30-user blind set t10 to t39 with a shuffled mix of 10 COMPLIANT, 10 NON_COMPLIANT, and 10 NOT_APPLICABLE users. Writes the hidden key to `bulk_labels_PRIVATE.csv` | Yes |
| `cleanup_bulk.py` | Removes the bulk users (MFA devices, console passwords, access keys, then the user). Only touches users tagged `project=team3-test` | Yes |
| `score_blind.py` | Scores the automated check and one or more manual audit sheets against the hidden key. Refuses to run if the key no longer matches the hash saved at build time | No |

## Install

```
py -m pip install -r scripts\TestScripts\requirements.txt
```

## Safety rules

- The build and cleanup scripts refuse to run unless the `APPROVED_ID` environment variable
  equals the account you are signed in to. Set it to the sandbox account's 12 digits in your
  own shell, and never write it in a file:
  ```
  $env:APPROVED_ID = "<SANDBOX_ID>"
  ```
- Passwords, access-key secrets, and MFA seeds are generated, used, and discarded. They are not printed or saved.
- Use these scripts only in an account the team owns.

## Running the blind test

1. **Build.** Run `build_bulk.py` with a profile for the sandbox. Run it first with `COUNT = 3` (a pilot) and check the result, then with `COUNT = 30`. The script writes the key to `bulk_labels_PRIVATE.csv`.
2. **Lock the key.** Right after the build, record its SHA-256 and the build time:
   ```
   Get-FileHash bulk_labels_PRIVATE.csv -Algorithm SHA256 | Tee-Object build-key-hash.txt
   ```
   Do not open the key until scoring.
3. **Audit.** The auditor fills in the audit sheet from the IAM console, without the key. Save and hash it.
4. **Run the checker** (`automation/mfa_checker/run_check.py`) with `--mask-account-id`.
5. **Score.**
   ```
   py score_blind.py --key bulk_labels_PRIVATE.csv --hash-file build-key-hash.txt `
       --checker <dir>\report.csv --checker-seconds <seconds> `
       --audits <audit sheet>.xlsx --out scoring-blind
   ```
   `score_blind.py` reads the audit columns by header name, so a swapped header does not produce wrong scores.
6. **Clean up.** After scoring:
   ```
   py cleanup_bulk.py --first 10 --count 30 --profile <profile>
   ```
   Also delete any access keys made for the test users.

## Do not commit

- `bulk_labels_PRIVATE.csv` before the blind test is scored. After scoring, the key is committed with the run's evidence as `answer-key.csv`.
- Real account IDs, access keys, passwords, or MFA seeds.
