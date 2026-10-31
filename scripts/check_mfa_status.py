#!/usr/bin/env python3
"""Check MFA status for every IAM user and, separately, for the root user.

Read-only. Required IAM permissions:
  iam:ListUsers, iam:GetLoginProfile, iam:ListMFADevices, iam:GetAccountSummary
  (the account check uses sts:GetCallerIdentity, which needs no IAM permission)

Control under test: every IAM user with a console password has at least one MFA
device registered. This script checks registered-device configuration only. It does
not test whether AWS blocks a sign-in or API call that lacks MFA.

Result per user:
  PASS  console password enabled AND at least one MFA device
  FAIL  console password enabled AND no MFA device
  N/A   no console password (not a console user)

Root MFA is reported separately. It is not part of the user-control result.

Account safety: you must pass --approved-account-id. The script confirms the active
credentials belong to that account BEFORE any IAM call, and refuses otherwise.

Usage examples:
  py check_mfa_status.py --approved-account-id 111122223333 --profile lab-readonly
  py check_mfa_status.py --approved-account-id 111122223333 --profile lab-readonly --format both
  py check_mfa_status.py --approved-account-id 111122223333 --show-names   # local use only!

By default user names are redacted (user-001, ...) and only the last four digits of the
account ID are written, so the output is safer for a public repo. Check it before
committing anyway.

Exit code: 0 = user control and root MFA both pass, 1 = at least one FAIL,
           2 = could not run (wrong account, AWS error, or no users returned).
"""

import argparse
import sys

from botocore.exceptions import BotoCoreError, ClientError

from mfa_common import (
    WrongAccountError,
    account_id_arg,
    make_iam_client,
    make_sts_client,
    print_table,
    redact_names,
    utc_now_iso,
    verify_account,
    write_outputs,
)


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
    parser.add_argument(
        "--approved-account-id",
        required=True,
        type=account_id_arg,
        help="12-digit ID of the sandbox account. The script refuses to run in any other account.",
    )
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

    # Account guard: runs before any IAM call.
    sts = make_sts_client(args.profile)
    try:
        account_masked = verify_account(sts, args.approved_account_id)
    except WrongAccountError as err:
        print(err, file=sys.stderr)
        return 2
    except (ClientError, BotoCoreError):
        print("Could not confirm which AWS account these credentials belong to. "
              "Check your profile and that your session has not expired. Nothing was checked.",
              file=sys.stderr)
        return 2

    iam = make_iam_client(args.profile)
    try:
        rows = collect_user_results(iam)
        root_ok = root_mfa_enabled(iam)
    except ClientError as err:
        code = err.response["Error"]["Code"]
        print(f"AWS error ({code}). Check that your profile has the read-only IAM "
              "permissions listed at the top of this script.", file=sys.stderr)
        return 2

    if not rows:
        print("No IAM users were returned, so nothing was checked. Refusing to report a result. "
              "Check the account and the profile's permissions.", file=sys.stderr)
        return 2

    if not args.show_names:
        rows = redact_names(rows)

    failures = [r for r in rows if r["result"] == "FAIL"]
    user_result = "FAIL" if failures else "PASS"
    root_result = "PASS" if root_ok else "FAIL"
    summary = {
        "checked_utc": utc_now_iso(),
        "account_id_masked": account_masked,
        "user_control": {
            "users_checked": len(rows),
            "console_users": sum(1 for r in rows if r["console_access"]),
            "failures": len(failures),
            "result": user_result,
        },
        "root_mfa": {"enabled": root_ok, "result": root_result},
        "overall": "PASS" if user_result == "PASS" and root_result == "PASS" else "FAIL",
        "names_redacted": not args.show_names,
    }

    print_table(rows, ["user", "console_access", "mfa_device_count", "result"])
    print()
    print(f"User control: {user_result}  ({len(failures)} failing of "
          f"{summary['user_control']['console_users']} console user(s))")
    print(f"Root MFA (reported separately, not part of the user-control result): {root_result}")
    print(f"Overall: {summary['overall']}")

    for path in write_outputs(rows, summary, out_dir, "mfa-status", args.format):
        print(f"Wrote {path}")

    return 0 if summary["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
