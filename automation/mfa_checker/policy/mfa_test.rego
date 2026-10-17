# Unit tests for policy/mfa.rego  -  run with:  opa test policy/ -v
# Cases T1-T5 match the team's labeled test-case table (Report 1, Section 4).

package mfa_test

import data.mfa

fixture := {
	"account_id": "123456789012",
	"scan_timestamp_utc": "2026-01-01T00:00:00+00:00",
	"users": [
		{"user_name": "t1", "console_access": true, "mfa_devices": ["arn:aws:iam::123456789012:mfa/t1"]},
		{"user_name": "t2", "console_access": true, "mfa_devices": []},
		{"user_name": "t3", "console_access": false, "mfa_devices": []},
		{"user_name": "t4", "console_access": true, "mfa_devices": []},
		{"user_name": "t5", "console_access": true, "mfa_devices": [
			"arn:aws:iam::123456789012:mfa/t5a",
			"arn:aws:iam::123456789012:mfa/t5b",
		]},
	],
}

# T1: console + MFA
test_t1_compliant if mfa.user_status.t1 == "COMPLIANT" with input as fixture

# T2: console, no MFA
test_t2_noncompliant if mfa.user_status.t2 == "NON_COMPLIANT" with input as fixture

# T3: no console password, outside the rule's scope (boundary case)
test_t3_not_applicable if mfa.user_status.t3 == "NOT_APPLICABLE" with input as fixture

# T4: MFA was deactivated, so the snapshot shows no devices
test_t4_noncompliant if mfa.user_status.t4 == "NON_COMPLIANT" with input as fixture

# T5: two devices
test_t5_compliant if mfa.user_status.t5 == "COMPLIANT" with input as fixture

fixture_report := r if r := mfa.report with input as fixture

test_noncompliant_list_is_sorted_and_exact if {
	fixture_report.noncompliant_users == ["t2", "t4"]
	fixture_report.noncompliant_count == 2
	fixture_report.total_users == 5
}

# Empty account: valid, empty report rather than an error
empty_report := r if r := mfa.report with input as {"account_id": "123456789012", "scan_timestamp_utc": "x", "users": []}

test_empty_account if {
	empty_report.total_users == 0
	empty_report.noncompliant_users == []
}

# Negative case: a user with console access and no devices must never be
# reported as compliant just because the device list is empty.
lone_status := r if r := mfa.user_status with input as {"account_id": "1", "users": [{"user_name": "u", "console_access": true, "mfa_devices": []}]}

test_empty_device_list_is_never_compliant if lone_status.u == "NON_COMPLIANT"
