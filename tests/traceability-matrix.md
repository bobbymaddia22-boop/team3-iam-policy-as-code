# Traceability Matrix: MFA Enforcement

Shows that every baseline requirement is covered by at least one test and has evidence.

| Requirement | Source | Test case(s) | Evidence file(s) | Latest status | Last run |
|-------------|--------|--------------|------------------|---------------|----------|
| R1: Root user MFA | [CIS control ID] | MFA-06 | | Not run | |
| R2: MFA for console users | [CIS control ID] | MFA-01, MFA-02, MFA-05, MFA-07 | | Not run | |
| R2/R3: MFA for sensitive API actions | CIS / NIST SP 800-63B | MFA-03, MFA-04 | | Not run | |
| R4: [Team requirement] | | | | Not run | |

## How to maintain this file

1. After each test run, update **Latest status**, **Evidence file(s)**, and **Last run**.
2. If a requirement has no test case, add one in `test-cases.md` and link it here.
3. If a test case has no requirement, either link it to one or question why the test exists.
