# Security Policy

This is a university capstone project that checks one AWS IAM control in a controlled lab
account. It is not a production security product. Please still report problems that could
expose someone's data or credentials.

## What to report

- A committed secret: an access key, a secret key, a session token, a password, or a private key.
- A real AWS account ID, user name, or email address in a file, a screenshot, or the commit history.
- Behavior that goes beyond the read-only design, for example any code path that changes IAM.
- A way to make the check report COMPLIANT for a user who has a console password and no MFA device.

## How to report

Use the repository's **Security** tab and choose **Report a vulnerability**. This sends the
report privately to the repository owner. Please do not open a public issue for a security
problem, and do not include real credentials in the report. Describe where the problem is
(file, line, or commit) and what you saw.

If the Security tab does not offer a private report, open an issue that says only that you
have a security concern and ask for a private way to send details. Do not put the details in the issue.

## What to expect

The team will read each report, confirm whether it is a real problem, and fix or remove the
exposed content. If a credential was exposed, the owner of the affected AWS account will be
asked to delete it first, because deleting a key is the only fix that works once it is public.

## Supported version

The version evaluated for the course is the tagged Week 12 release named in the README.
Other commits are not supported separately.

## Scope and limits

- The tool reads IAM state in a lab account. It does not test whether AWS blocks a sign-in or
  API call that lacks MFA.
- It is meant for the team's own sandbox accounts. Do not run it against accounts you do not own.
- See `docs/security-analysis.md` for the assets, threats, controls, residual risks, and
  safe-use limits.
