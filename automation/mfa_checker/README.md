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

## Not yet verified against real AWS

- The scripts have only run against the moto simulator. Run them in the real sandbox
  and compare with the IAM console before using any result as evidence.
- Confirm that `ListMFADevices` returns passkey and security-key (FIDO) devices as
  expected; test that case in the sandbox before relying on it.
- Moto accepted placeholder MFA codes; real virtual MFA setup needs real TOTP codes.
- Point-in-time only: a user changed after collection is not seen until the next run.

`examples/simulated_run/` shows the report format from a simulated run and is **not**
project evidence.
