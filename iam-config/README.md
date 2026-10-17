# IAM configuration

IAM policy documents used in the lab, such as MFA-enforcement policies under test and
read-only permissions for scanning.

The automated check's read-only scanner permissions are kept next to the tool in
`automation/mfa_checker/scanner-iam-policy.json`. Add other policy JSON files here as
the team creates them, and replace real account IDs with placeholders.
