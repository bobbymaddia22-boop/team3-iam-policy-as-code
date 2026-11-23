# Automated output for Run 01

The original `report.json` and `report.csv` from this run were not saved, so this folder has no
output files and there is no hash list for Run 01.

## What shows the run instead

- The screenshots in `../screenshots/` show the CloudShell session, the tool versions, the script
  run, and the `report.csv` output. The run time quoted in `../findings.md` comes from them.
- Run 02 (`../../run-02/`) and the practice-account run were made later with the same checker and
  have saved report files and hash lists.

## Do not commit

The checker also writes `snapshot.json`, which contains the full account ID. The repository's
`.gitignore` excludes it, so it should not appear in GitHub Desktop. Check that it does not.