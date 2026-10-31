# Test Results: MFA Configuration Check

Copy this file for each run and rename it
`results-YYYY-MM-DD-<tester-initials>.md`. Do not edit the template itself.
The run write-up itself lives in `evidence/run-NN/findings.md`. This file records the
test-case outcomes.

## Run details

| Field | Value |
|-------|-------|
| Date | [YYYY-MM-DD] |
| Tester | [Name] |
| Run folder | `evidence/run-[NN]/` |
| Environment | Sandbox account `111122223333`, [region] |
| Identity used | [root, console identity, or read-only scanner] |
| Blind manual audit? | [Yes or No. If yes, who audited and who held the answer key] |
| Manual evidence source | [IAM console or credential report] |
| Tool versions | Python [x], boto3 [x], OPA [x] |
| Repository version tested | [commit hash or tag] |
| Test plan version | [e.g., 0.2] |

## Results: labeled population

| Test ID | User | Expected | Automated actual | Manual actual | Status | Evidence file | Notes |
|---------|------|----------|------------------|---------------|--------|---------------|-------|
| T1 | t1 | COMPLIANT | | | Pass / Fail / Blocked | | |
| T2 | t2 | NON_COMPLIANT | | | Pass / Fail / Blocked | | |
| T3 | t3 | NOT_APPLICABLE | | | Pass / Fail / Blocked | | |
| T4 | t4 | NON_COMPLIANT | | | Pass / Fail / Blocked | | |
| T5 | t5 | COMPLIANT | | | Pass / Fail / Blocked | | |

## Scoring

Paste the output of `scripts\score_results.py`, or link to `scoring-results.md` in the run folder.

| Measure | Automated | Manual |
|---------|-----------|--------|
| Exact status matches | | |
| Precision / recall / false-positive rate | | |
| Time (state how it was measured) | | |

## Results: other cases run

| Test ID | Expected | Actual | Status | Evidence file | Notes |
|---------|----------|--------|--------|---------------|-------|
| | | | Pass / Fail / Blocked | | |

## Evidence hashes

| File | SHA-256 |
|------|---------|
| | |

## Summary

- **Passed:** [n]
- **Failed:** [n]
- **Blocked:** [n]

## Defects and follow-up

| Issue | Description | Linked GitHub issue |
|-------|-------------|---------------------|
| | | |

## Sanitization check (complete before committing)

- [ ] No access keys, secrets, or tokens in any file
- [ ] Account IDs, access key IDs, ARNs, and user names replaced with placeholders or masked
- [ ] Screenshots redacted (console header, email, account alias) and checked at full size
- [ ] No `snapshot.json` and nothing from `output-private/`
- [ ] No real user or organizational data

## Sign-off

Tester: [Name]  Reviewer: [Name]  Date: [YYYY-MM-DD]
