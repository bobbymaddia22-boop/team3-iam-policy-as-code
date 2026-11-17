# MFA Enforcement Check (AWS IAM)

Team 3: Cloud Identity and Policy-as-Code Assurance. Role: Policy-as-Code Developer.

A read-only collector gathers IAM facts, an Open Policy Agent (OPA) policy decides
compliance, and a report records each decision.

```
AWS IAM  ->  collect_iam_state.py  ->  snapshot.json  ->  policy/mfa.rego (OPA)  ->  report.json / report.csv
```

## The rule

Every IAM user with a **console password** must have **at least one MFA device**.
Users without a console password are `NOT_APPLICABLE` (test case T3). The positive
class when scoring is `NON_COMPLIANT`.

| Status | Meaning |
| --- | --- |
| `COMPLIANT` | console password and at least one MFA device |
| `NON_COMPLIANT` | console password and no MFA device |
| `NOT_APPLICABLE` | no console password |

## Safety properties

| Requirement | How it is met |
| --- | --- |
| SR2 read-only | Only `ListUsers`, `ListMFADevices`, `GetLoginProfile` (see `scanner-iam-policy.json`), plus `sts:GetCallerIdentity`. A test fails if any other call is made. |
| SR3 right account | `--approved-account-id` is checked first. Mismatch exits with code 2 before any IAM call. |
| SR4 traceable | Every report has a UTC timestamp and the account ID. `--mask-account-id` keeps only the last 4 digits for public evidence. |
| Fail closed | Any AWS error exits with code 3 and writes no snapshot or report. |

Exit codes: 0 ok, 2 wrong account, 3 AWS error, 4 OPA error.

## Run it (sandbox account only)

```bash
pip install boto3
# install the opa binary from https://github.com/open-policy-agent/opa/releases
python run_check.py --approved-account-id <SANDBOX_ID> --outdir evidence/run1
# for files you will publish:
python run_check.py --approved-account-id <SANDBOX_ID> --outdir evidence/run1 --mask-account-id
```

`report.json` also records seconds for collect, evaluate, and total, for comparison
with the manual audit.

## Test it (no AWS account needed)

```bash
pip install moto[iam,sts] pytest
opa test policy/ -v                 # 8 Rego unit tests
OPA_BIN=/path/to/opa pytest -v tests/   # 8 end-to-end tests on simulated IAM
```

Tested with Python 3.13, boto3 1.43.111, moto 5.2.3, OPA 1.21.1.

## Sandbox results

First sandbox run: 5 of 5 users matched the expected labels in 0.56 seconds. Later runs under the restricted scanner identity matched 8 of 8 users. A wrong approved account ID exits with code 2 and makes no IAM call. A denied permission exits with code 3 and writes no report.

## Known limits

- Small, hand built user set. Results show the rule works on those cases, not how it performs at scale.
- The check shows that an MFA device is registered. It does not test whether AWS blocks a sign in or API call without MFA.
- It covers IAM users only. IAM Identity Center users are outside it.
- It is a snapshot of one moment.
- A partial permission denial and a write attempt under the scanner identity have not been tested.
- How passkeys and security keys appear in the device list is unverified.
- `--mask-account-id` only changes report files. Console screenshots and AWS error text can still show the full account ID, so check every screenshot before committing.

