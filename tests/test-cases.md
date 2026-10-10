# Test Cases: MFA Enforcement (AWS IAM)

All identities, account IDs, and ARNs below are placeholders. Update them to match
the lab setup, and keep real values out of this public repo.

## Summary

| ID | Title | Requirement | Status |
|----|-------|-------------|--------|
| MFA-01 | Console sign-in with MFA enabled | R2 | Not run |
| MFA-02 | Console sign-in without MFA | R2 | Not run |
| MFA-03 | API/CLI action without MFA is denied | R2, R3 | Not run |
| MFA-04 | API/CLI action with MFA session is allowed | R2, R3 | Not run |
| MFA-05 | MFA device removed or deactivated | R2 | Not run |
| MFA-06 | Root user MFA status | R1 | Not run |
| MFA-07 | Credential report shows MFA for all console users | R2 | Not run |

Status values: Not run / Pass / Fail / Blocked

---

## MFA-01: Console sign-in with MFA enabled

- **Requirement:** R2
- **Preconditions:** `test-user-mfa` exists, has a console password and an active MFA device.
- **Steps:**
  1. Open the sign-in page in a private browser window.
  2. Sign in as `test-user-mfa`.
  3. Enter the MFA code when prompted.
- **Expected result:** Sign-in succeeds only after the MFA code is provided.
- **Actual result:** [fill in]
- **Status:** Not run
- **Evidence:** [filename in /evidence]

## MFA-02: Console sign-in without MFA

- **Requirement:** R2
- **Preconditions:** `test-user-nomfa` exists, has a console password, and has no MFA device.
- **Steps:**
  1. Sign in as `test-user-nomfa`.
  2. Attempt to use a service covered by the MFA-required policy.
- **Expected result:** Access to sensitive actions is denied or restricted until MFA is configured.
- **Actual result:** [fill in]
- **Status:** Not run
- **Evidence:** [filename in /evidence]

## MFA-03: API/CLI action without MFA is denied

- **Requirement:** R2, R3
- **Preconditions:** The deny-without-MFA policy is attached to the test user or group.
- **Steps:**
  1. Configure a CLI profile for the test user using a session with no MFA.
  2. Run a sensitive action covered by the policy (document the exact command).
- **Expected result:** The request is denied with an access denied error.
- **Actual result:** [fill in]
- **Status:** Not run
- **Evidence:** [filename in /evidence]

## MFA-04: API/CLI action with MFA session is allowed

- **Requirement:** R2, R3
- **Preconditions:** Same as MFA-03, and the user has an active MFA device.
- **Steps:**
  1. Obtain a temporary session using the MFA device (for example, with `aws sts get-session-token`).
  2. Run the same action as MFA-03 using the temporary credentials.
- **Expected result:** The request succeeds.
- **Actual result:** [fill in]
- **Status:** Not run
- **Evidence:** [filename in /evidence]

## MFA-05: MFA device removed or deactivated

- **Requirement:** R2
- **Preconditions:** `test-user-mfa` is working per MFA-01.
- **Steps:**
  1. Deactivate the user's MFA device in IAM.
  2. Repeat the sensitive action from MFA-03.
- **Expected result:** Enforcement still holds; access is denied without MFA.
- **Actual result:** [fill in]
- **Status:** Not run
- **Evidence:** [filename in /evidence]
- **Cleanup:** Re-enable the MFA device after the test.

## MFA-06: Root user MFA status

- **Requirement:** R1
- **Preconditions:** Access to the account summary in a controlled way.
- **Steps:**
  1. Check the root user's MFA status (for example, via the IAM dashboard security status or the account summary).
- **Expected result:** MFA is enabled for the root user.
- **Actual result:** [fill in]
- **Status:** Not run
- **Evidence:** [filename in /evidence, sanitized]

## MFA-07: Credential report shows MFA for all console users

- **Requirement:** R2
- **Preconditions:** Permission to generate the IAM credential report.
- **Steps:**
  1. Generate and download the credential report.
  2. For every user with `password_enabled` = true, check that `mfa_active` = true.
- **Expected result:** No console user has `mfa_active` = false.
- **Actual result:** [fill in]
- **Status:** Not run
- **Evidence:** [sanitized report in /evidence]
