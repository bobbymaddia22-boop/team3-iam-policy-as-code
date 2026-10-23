# Manual Audit Procedure: IAM Console-User MFA Check

**Version:** 0.1 (draft)
**Used by:** `tests/test-plan.md`, section 6
**Control:** Every IAM user with a console password has at least one MFA device.

## 1. Rules for the auditor

- Audit the same five users the automated check audits. Do not add, remove or change users.
- Do **not** open `evidence/run-01/labeled-population.csv` or any automated result file until your results file is saved.
- Use only the evidence source named in section 2. Record anything else you consulted.
- Read-only. Do not change any user, password or MFA device.

## 2. Evidence source

Source used for this run: **IAM console, Users list plus each user's Security credentials tab (console access and assigned MFA devices)**

Account: sandbox, ID shown as `111122223333` in the repository.
Identity used to view it: **[confirm]**

## 3. Steps

1. Confirm you are signed in to the sandbox account. Note the last four digits of the account ID in your notes.
2. Start the stopwatch. Record the start time.
3. Get the user list from the evidence source above.
4. For each user, record two facts:
   - Does the user have a console password? (yes / no)
   - How many MFA devices are registered? (number)
5. Decide the status for each user:
   - Console password = no → `NOT_APPLICABLE`
   - Console password = yes and one or more MFA devices → `COMPLIANT`
   - Console password = yes and zero MFA devices → `NON_COMPLIANT`
6. Write the results to `evidence/run-01/manual-audit.csv` with the columns below.
7. Save the file, then stop the stopwatch. Record the stop time.
8. Compute the SHA-256 hash of the file and record it in `evidence/run-01/findings.md`.
9. Only now open the labeled population or the automated results for scoring.

## 4. Results file

```
user_name,console_password,mfa_devices,manual_status
```

One row per user. Add a separate line in `findings.md` for total elapsed time (stop minus start) and any notes about difficulty.

## 5. Timing boundaries

| Starts | Stops |
|--------|-------|
| Auditor begins step 2 | Auditor saves the results file in step 6 |

Not included: account sign-in, labeling the population, scoring, and writing the findings. The automated method is timed over the equivalent span (command start to results file written) so the two numbers cover the same work.

## 6. Recording problems

Note any ambiguity (for example, a user whose MFA device was removed) and how you resolved it. Do not change a result after seeing the ground truth. If a correction is needed, record the original and the corrected value and the reason.
