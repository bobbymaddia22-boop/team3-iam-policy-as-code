# Third-Party Software and Reuse Notes

This project reuses open-source tools and cites public standards. This file records what we use, under what license, and how we checked.


## 1. Software dependencies

| Tool | Used for | License | Version checked | How checked |
|------|----------|---------|-----------------|-------------|
| boto3 | AWS API calls in `scripts/` and `automation/mfa_checker/` | Apache-2.0 | Latest on PyPI at check time: 1.43.118 (released 2026-10-22). Team's installed version: Team's installed version: 1.43.126 | License field on the project's PyPI page, https://pypi.org/project/boto3/ |
| moto | Local simulation of IAM for tests | Apache-2.0 | Latest on PyPI at check time: 5.2.4 (released 2026-10-11). Team's installed version: 	Team's installed version: 5.2.5 | License field on the project's PyPI page, https://pypi.org/project/moto/ |
| pytest | Running unit tests | MIT | Latest on PyPI at check time: 9.1.1 (released 2026-06-19). Team's installed version: Team's installed version: 9.2.0 | License field on the project's PyPI page, https://pypi.org/project/pytest/ |
| Open Policy Agent (OPA) | Evaluating `mfa.rego` | Apache-2.0 |Team's installed version: 1.22.2 (Run 01 used 1.21.1 in CloudShell) | License shown on the project's GitHub page, https://github.com/open-policy-agent/opa |

Notes:
- Dependencies are installed from their package sources at run time. No third-party source code is copied into this repository.
- The `opa` binary and the Python virtual environment are not committed (see `.gitignore`).
- If a version in use differs from the version checked, re-check before the final submission.

## 2. Standards and documents

| Document | How we use it |
|----------|---------------|
| CIS AWS Foundations Benchmark | Cited as the source of the control. Control text is not copied into the repository. |
| NIST SP 800-63B-4 | Cited as background. Not reproduced. |
| NIST SP 800-53A Rev. 5 | Cited as background. Not reproduced. |

## 3. Test data

All test data is synthetic. The test users (t1 to t39) were created for this project in sandbox AWS accounts. No real people, employer data, or production accounts are involved. Account IDs shown in the repository are placeholders (`111122223333`).

## 4. Code written by the team

- Python scripts in `scripts/` were written by Carlton Ferdinand
- The OPA pipeline in `automation/mfa_checker/` was written by Carlton Ferdinand.
- The build, cleanup and scoring scripts in `scripts/TestScripts/` were written by Bobby Maddia.

## 5. Reuse check (before adding anything new)

Before adding code, text, images, or data from outside the team:
1. Identify the source and its license. If there is no license, do not copy it.
2. Confirm the license allows our use and note any attribution it requires.
3. Add a row to this file with the source, license, and date checked.
4. If unsure, ask Dana DiLeo before committing.
