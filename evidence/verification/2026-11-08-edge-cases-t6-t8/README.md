# Edge cases t6 to t8

- Identity: read-only scanner (3-action policy), so this is not an admin-identity run.
- Tools: Python 3.13.17, OPA 1.22.2.

## Edge cases

| User | Setup | Expected |
|---|---|---|
| t6 | Console password and MFA device set, then the password removed | NOT_APPLICABLE |
| t7 | Console password, must reset at next sign-in, never used, no MFA | NON_COMPLIANT |
| t8.test+mfa,Case=A@team3 | Special characters in the name (+ @ , and mixed case), console password, no MFA | NON_COMPLIANT |

## Result

8 of 8 exact matches; TP=4 (t2, t4, t7, t8), FP=0, FN=0, TN=4. Run time about 1.6 s for 12 users.

## Notes

- t6 shows the rule depends on the console password, not on whether an MFA device exists.
- t7 assumes no grace period: a user with a password who has never signed in is still NON_COMPLIANT. The team should record this decision.
- t8 shows the comma in the username stays inside one quoted CSV column and the user is not skipped.
- report.csv excludes non-test users (bobby-admin, scanner-readonly, validation-readonly, noperm-test) so every user is in the answer key.
- The credential-report freshness test (t9) and the 30-user bulk set are not part of this run.
