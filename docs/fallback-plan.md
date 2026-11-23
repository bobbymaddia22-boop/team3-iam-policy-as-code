# Fallback Plan

This plan says what the team does if the live sandbox AWS account is unavailable, a run fails, or a teammate's results can't be reproduced. It keeps a valid comparison of the automated and manual methods and states what the reduced version can no longer show.

## 1. Triggers

Switch to the fallback if any of these happens and is not fixed within 2 days:
- The sandbox account is locked, suspended, or out of credits.
- The labeled test users cannot be created or restored.
- The live run's original artifacts (`report.json`, `report.csv`) cannot be recovered or reproduced.
- The read-only scanner identity cannot be created.

The Testing and Validation Lead declares the switch in the team channel and records it in the run's findings file under `evidence/`.

## 2. What stays the same

- The same labeled users and the same expected statuses (t1 to t8, and the 30-user blind set t10 to t39).
- Both methods audit the same population and the same data.
- The manual auditor stays blind to the labels until the results file is saved and hashed.
- Scoring uses the same confusion matrix, precision, recall, and false-positive rate.
- Timing boundaries stay as defined in `tests/manual-audit-procedure.md`.

## 3. What changes

| Item | Live run | Fallback run |
|------|----------|--------------|
| Data source | Sandbox AWS account | Simulated IAM (moto), populated with the same labeled users |
| Automated check | Runs against the live account | Runs against the simulated account using the same collector and policy |
| Manual audit | Reads the IAM console | Reads a saved IAM credential report file generated from the same simulated account (the console is not available) |
| Account-ID guard | Checked against the sandbox ID | Checked against the simulated account ID |

The fallback manual audit and the automated check read the same underlying data, so the comparison is mostly about reading effort and accuracy of classification, not independence of sources. The findings must say this.

## 4. Conclusions the fallback cannot support

A simulated account does not show:
- How real IAM behaves (for example, the timing of the credential report, or console behavior).
- That the read-only scanner permissions are sufficient in a real account.
- Anything about sign-in or API enforcement of MFA.
- Timing that represents a live run. Fallback timings are labeled as simulated.
- Whether the results reproduce in a different real account.

Conclusions about whether the classification logic gives the expected status for the labeled cases remain supportable.

## 5. Minimum evidence for a fallback run

- The scripts or commands used, with the simulator version.
- The results file from each method, with SHA-256 hashes.
- The labeled population file.
- A filled-in findings file stating that this was a fallback run and listing section 4.


