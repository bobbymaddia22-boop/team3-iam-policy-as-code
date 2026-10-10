#!/usr/bin/env python3
"""Check MFA status for every IAM user and for the root user. (Test cases MFA-01/02/06)

Read-only. Required IAM permissions:
  iam:ListUsers, iam:GetLoginProfile, iam:ListMFADevices, iam:GetAccountSummary

Result per user:
  PASS  console password enabled AND at least one MFA device
  FAIL  console password enabled AND no MFA device
  N/A   no console password (not a console user)

Usage examples:
  python check_mfa_status.py --profile lab-readonly
  python check_mfa_status.py --profile lab-readonly --format both
  python check_mfa_status.py --profile lab-readonly --show-names   # local use only!

By default user names are redacted (user-001, ...) and no ARNs or account IDs are
written, so the output is safer for a public repo. Check it before committing anyway.
Exit code: 0 = all checks pass, 1 = at least one FAIL, 2 = could not run.
"""

import argparse
import sys

from botocore.exceptions import ClientError

from mfa_common import make_iam_client, print_table, redact_names, utc_now_iso, write_outputs


def evaluate(console_access, mfa_device_count):
    if not console_access:
        return "N/A"
    return "PASS" if mfa_device_count > 0 else "FAIL"


def has_console_password(iam, user_name):
    try:
        iam.get_login_profile(UserName=user_name)
        return True
    except ClientError as err:
        if err.response["Error"]["Code"] == "NoSuchEntity":
            return False
        raise


def count_mfa_devices(iam, user_name):
    total = 0
    for page in iam.get_paginator("list_mfa_devices").paginate(UserName=user_name):
        total += len(page["MFADevices"])
    return total


def collect_user_results(iam):
    rows = []
    for page in iam.get_paginator("list_users").paginate():
        for user in page["Users"]:
            name = user["UserName"]
            console = has_console_password(iam, name)
            devices = count_mfa_devices(iam, name)
            rows.append(
                {
                    "user": name,
                    "console_access": console,
                    "mfa_device_count": devices,
                    "result": evaluate(console, devices),
                }
            )
    return rows


def root_mfa_enabled(iam):
    summary = iam.get_account_summary()["SummaryMap"]
    return summary.get("AccountMFAEnabled", 0) == 1


def main():
    parser = argparse.ArgumentParser(description="Check IAM MFA status (read-only).")
    parser.add_argument("--profile", help="AWS CLI profile name (use a read-only lab profile)")
    parser.add_argument("--format", choices=["json", "csv", "both"], default="json")
    parser.add_argument("--out-dir", help="Where to write results")
    parser.add_argument(
        "--show-names",
        action="store_true",
        help="Keep real user names in output. Local use only; do NOT commit this output.",
    )
    args = parser.parse_args()

    out_dir = args.out_dir or ("output-private" if args.show_names else "sample-output")
    iam = make_iam_client(args.profile)

    try:
        rows = collect_user_results(iam)
        root_ok = root_mfa_enabled(iam)
    except ClientError as err:
        code = err.response["Error"]["Code"]
        print(f"AWS error ({code}). Check that your profile has the read-only IAM "
              "permissions listed at the top of this script.", file=sys.stderr)
        return 2

    if not args.show_names:
        rows = redact_names(rows)

    failures = [r for r in rows if r["result"] == "FAIL"]
    summary = {
        "checked_utc": utc_now_iso(),
        "users_checked": len(rows),
        "console_users": sum(1 for r in rows if r["console_access"]),
        "failures": len(failures),
        "root_mfa_enabled": root_ok,
        "overall": "PASS" if not failures and root_ok else "FAIL",
        "names_redacted": not args.show_names,
    }

    print_table(rows, ["user", "console_access", "mfa_device_count", "result"])
    print()
    print(f"Root MFA enabled: {root_ok}")
    print(f"Overall: {summary['overall']}  ({len(failures)} failing user(s))")

    for path in write_outputs(rows, summary, out_dir, "mfa-status", args.format):
        print(f"Wrote {path}")

    return 0 if summary["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
