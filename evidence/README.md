# Evidence

Redacted records of test runs for the MFA enforcement control. Every claim in the project
reports should point to a file in this folder.

## Contents

| Path | What it is |
|------|------------|
| `run-template.md` | Blank findings record. Copy it for each new run. |
| `run-01/` | First run: the labeled population (t1 to t5), the automated check, and the manual audit |

## What each run folder contains

| File or folder | Purpose |
|----------------|---------|
| `findings.md` | The write-up: population, automated results, manual results, disagreements, limits |
| `labeled-population.csv` | The answer key: the expected result for every test user |
| `manual-audit.csv` | The manual auditor's verdict and time for every test user |
| `automated/` | Masked output files from the automated check (`report.json`, `report.csv`) |
| `screenshots/` | Redacted console and terminal screenshots |

## Adding a new run

1. Copy `run-01/` to `run-02/` (or the next number) and clear the files you will replace.
2. Copy `run-template.md` to `run-02/findings.md` and fill in every row.
3. Add the masked automated output, the manual audit file, and screenshots.
4. Record the SHA-256 hash of each output file in `findings.md` (see below).
5. Complete the checklist below, then commit on a branch and open a pull request.

## Blind runs

A blind run tests whether a method gives the right answer when the person running it does not
know how the users are configured. For a blind run:

- The person who built the users keeps the answer key (`labeled-population.csv`) out of the
  auditor's view until the manual audit is finished.
- Add `labeled-population.csv` to the run folder only after the audit, and say in `findings.md`
  that the run was blind.
- Have the manual audit done by someone who did not build or label the population.

## Recording file hashes

A hash lets a reader confirm that an evidence file was not changed after the run. In Windows
PowerShell, from the run folder:

```
Get-FileHash -Algorithm SHA256 .\automated\report.json
```

Copy the result into the evidence files table in `findings.md`. If a file is redacted before it is
committed, record the hash of the original, say that the committed copy is redacted, and keep the
original with the Environment Lead.

## Naming

Runs are numbered `run-01`, `run-02`, and so on. Screenshots use
`NN-short-description.png`, for example `01-iam-users-list.png`.

## Never commit here

- Raw `snapshot.json` files (they contain the full AWS account ID)
- Access keys, secret keys, session tokens, or passwords
- Unredacted screenshots or output with real account IDs, access key IDs, ARNs, usernames, or emails

## Before committing a file

- [ ] Account IDs, access key IDs, ARNs, and usernames replaced with placeholders (or masked)
- [ ] Console header, account alias, and email addresses blurred in screenshots
- [ ] Only controlled lab data
- [ ] Every number in `findings.md` can be traced to a file in the run folder
