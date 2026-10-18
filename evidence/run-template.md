# Run NN: [short description of the scenario or obstacle]

| | |
|---|---|
| **Control tested** | MFA is enabled for every IAM user who has a console password |
| **Environment** | Team 3 AWS sandbox (account ID masked); [where the check was run] |
| **Population** | [number of users, who built them, and how] |
| **Blind test?** | [Yes: the auditor did not know the user configurations / No] |
| **Automated method** | [collector + OPA rule, commit or version; who ran it] |
| **Tool versions** | [Python, boto3, OPA] |
| **Run identity** | [which AWS identity ran the check: read-only scanner, administrator, or root] |
| **Data source** | [live IAM API calls / credential report / AWS Config rule] |
| **Manual method** | [who audited; evidence source: console or credential report] |
| **Run date and time (UTC)** | [YYYY-MM-DD HH:MM] |

## 1. Labeled population

Is the population built, and does it match the answer key in `labeled-population.csv`?

[Yes / No, with details of any user that does not match.]

## 2. Automated results

| Measure | Value |
|---------|-------|
| Users scanned | |
| Flagged noncompliant | |
| Compliant | |
| Not applicable | |
| True positives / false positives | |
| False negatives / true negatives | |
| Known noncompliant control users flagged | |
| Run time (seconds) | |

Raw output: `automated/`

## 3. Manual audit results

| Measure | Value |
|---------|-------|
| Users audited | |
| Flagged noncompliant | |
| True positives / false positives | |
| False negatives / true negatives | |
| Total time (minutes) | |

Raw record: `manual-audit.csv`

## 4. Disagreements

[List every user where the automated result, the manual result, and the answer key do not
all agree. For each one: what each method said, the cause, and the fix. Write "None" if all
three agree.]

## Limits of this run

[What this run cannot show.]

## Evidence files

| File | SHA-256 |
|------|---------|
| | |
