# MFA enforcement policy for AWS IAM users
# Team 3 - Cloud Identity and Policy-as-Code Assurance
#
# Rule (derived from the CIS AWS Foundations Benchmark IAM recommendation):
#   every IAM user with a console password must have at least one MFA device.
#
# Input: the JSON snapshot written by collect_iam_state.py
#   { "account_id": "...", "users": [
#       { "user_name": "...", "console_access": true|false,
#         "mfa_devices": ["serial", ...] } ] }
#
# Query: data.mfa.report

package mfa

# The rule only applies to users who can sign in to the console.
requires_mfa(user) if user.console_access == true

status_of(user) := "NON_COMPLIANT" if {
	requires_mfa(user)
	count(user.mfa_devices) == 0
}

status_of(user) := "COMPLIANT" if {
	requires_mfa(user)
	count(user.mfa_devices) > 0
}

# Users without a console password are outside this rule's scope (test case T3).
status_of(user) := "NOT_APPLICABLE" if not requires_mfa(user)

user_status[user.user_name] := status_of(user) if some user in input.users

noncompliant_users := sort([name | some name, s in user_status; s == "NON_COMPLIANT"])

report := {
	"account_id": input.account_id,
	"scan_timestamp_utc": input.scan_timestamp_utc,
	"total_users": count(input.users),
	"noncompliant_count": count(noncompliant_users),
	"noncompliant_users": noncompliant_users,
	"user_status": user_status,
}
