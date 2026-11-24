# Evidence

Redacted records of test runs for the MFA configuration check. Every claim in the project
reports should point to a file in this folder.

## Contents

| Path | What it is |
|------|------------|
| `run-template.md` | Blank findings record. Copy it for each new run. |
| `run-01/` | **Run 01**: the first run. Labeled population t1 to t5 in the team sandbox, the automated check, and a manual audit (2026-10-05). |
| `run-02/edge-cases-t6-t8/` | **Run 02**: the population extended to t1 to t8 (new edge cases t6 to t8), scored in Bobby Maddia's own sandbox account under the read-only scanner identity. Not blind. |
| `run-03/blind-30-user-test/` | **Run 03**: the blind test. 30 users (t10 to t39) with hidden shuffled labels, scored for the automated check and a manual audit. |
| `support/practice-account-run/` | The first rebuild of t1 to t5 in the sandbox account, run under an admin identity (before Run 02). |
| `support/scanner-identity-and-negative-tests/` | Least-privilege run under the read-only scanner identity, plus the wrong-account and denied-permission tests. |
| `support/credential-report-cross-check/` | Comparison of the automated check with the AWS credential report for the same account (12 users). |


## What each run folder contains

| File or folder | Purpose |
|----------------|---------|
| `findings.md` | The write-up: population, automated results, manual results, disagreements, limits |
| `SHA256SUMS.txt` | The SHA-256 hash of every committed file in the run, written by the command below |
| `scoring-results.md` | Output of `scripts/score_results.py` for the run |
| `labeled-population.csv` | The answer key: the expected result for every test user |
| `manual-audit.csv` | The manual auditor's observations and verdict for every test user |
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

To hash every file in a run folder and write the list to `SHA256SUMS.txt`, run this in PowerShell from the run folder (for example `evidence\run-03\blind-30-user-test`). It writes the list with forward slashes and LF line endings, so the same list verifies on Windows, Mac and Linux:

```
$lines = Get-ChildItem -Recurse -File | Where-Object { $_.Name -ne "snapshot.json" -and $_.Name -ne "SHA256SUMS.txt" } | Sort-Object FullName | ForEach-Object { $rel = $_.FullName.Substring((Get-Location).Path.Length+1).Replace('\','/'); "$((Get-FileHash $_.FullName -Algorithm SHA256).Hash)  $rel" }
[IO.File]::WriteAllText("$PWD\SHA256SUMS.txt", (($lines -join "`n") + "`n"))
```

Line endings matter, because Git can change them and that changes the hash. Run this from a fresh clone, not from a folder you edited on Windows, and add the run folder to `.gitattributes` with `-text` before you commit (see the existing `evidence/run-03/**` line).

```

In Command Prompt, use `certutil -hashfile <file> SHA256` for one file at a time. Copy the result into the evidence files table in `findings.md`. If a file is redacted before it is
committed, record the hash of the original, say that the committed copy is redacted, and keep the
original with the Environment Lead.

## Naming

Numbered runs are `run-01`, `run-02`, and so on. Supporting evidence goes under `support/` in a folder named for what it shows. Screenshots use
`NN-short-description.png`, for example `01-iam-users-list.png`.

## Never commit here

- Raw `snapshot.json` files (they contain the full AWS account ID)
- Access keys, secret keys, session tokens, or passwords
- Unredacted screenshots or output with real account IDs, access key IDs, ARNs, usernames, or emails
- Anything from `output-private/`

## Before committing a file

- [ ] Account IDs, access key IDs, ARNs, and usernames replaced with placeholders (or masked)
- [ ] Console header, account alias, and email addresses blurred in screenshots, and the image checked at full size (a small preview can hide an unmasked ID)
- [ ] Animated images (GIF) checked frame by frame
- [ ] Only controlled lab data
- [ ] Every number in `findings.md` can be traced to a file in the run folder
