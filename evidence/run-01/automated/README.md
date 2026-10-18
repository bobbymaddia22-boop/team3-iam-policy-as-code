# Automated output (add files here)

Put the output of the automated check for this run in this folder:

- `report.json` (per-user decisions, timestamp, account ID, and timings)
- `report.csv` (one row per user)

## Where the original files are

The first run was made by Steve Bilali in AWS CloudShell, so the original files are in his
CloudShell session, in the folder he passed as `--outdir`. To download them, open CloudShell, choose
**Actions, then Download file**, enter the file's path, and repeat for the second file. Use the
original files if you can, because they carry the 0.56 second timing quoted in `../findings.md`.

If the originals are gone, rerun the check and update the run time in `findings.md` to match the
new `report.json`. From the `automation/mfa_checker` folder, in the sandbox account only:

```
python run_check.py --approved-account-id <SANDBOX_ID> --outdir ../../evidence/run-01/automated --mask-account-id
```

## Check for the account ID

Open `report.json` before committing. The account ID should show only its last four digits.

If the original shows the full ID, do not edit it by hand, because that changes the evidence.
Keep the original privately with the Environment Lead, record its SHA-256 hash in `findings.md`,
and commit a redacted copy that is labeled as redacted.

## Do not commit

The run also writes `snapshot.json`, which contains the full account ID. The repository's
`.gitignore` excludes it, so it should not appear in GitHub Desktop. Check that it does not.
