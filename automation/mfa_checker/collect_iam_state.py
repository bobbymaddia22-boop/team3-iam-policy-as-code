#!/usr/bin/env python3
"""
IAM state collector (read-only)
--------------------------------
Team 3 - Cloud Identity and Policy-as-Code Assurance
Role: Policy-as-Code Developer

Gathers the facts needed to judge MFA enforcement for IAM users and writes
them to a JSON snapshot. It makes NO compliance decision; that is done by the
OPA policy in policy/mfa.rego, which reads this snapshot as `input`.

Safety properties (map to the team's security requirements):
  SR2  Only read-only IAM calls are made: ListUsers, ListMFADevices,
       GetLoginProfile (plus sts:GetCallerIdentity).
  SR3  The account ID is checked against --approved-account-id BEFORE any IAM
       call. A mismatch aborts with exit code 2 and writes nothing.
  SR4  Every snapshot records a UTC timestamp and the account ID.
  Fail closed: any AWS error aborts the run (exit code 3) and no snapshot is
       written, so a failed scan can never look like a clean one.

Usage:
    python collect_iam_state.py --approved-account-id 123456789012 \
        --out evidence/snapshot.json

Use credentials for the team's sandbox account only.
"""

import argparse
import json
import sys
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError

EXIT_OK = 0
EXIT_WRONG_ACCOUNT = 2
EXIT_AWS_ERROR = 3


class WrongAccountError(Exception):
    """Raised when the active credentials belong to an unapproved account."""


def verify_account(sts_client, approved_account_id):
    """Return the caller's account ID, or raise if it is not the approved one."""
    actual = sts_client.get_caller_identity()["Account"]
    if actual != approved_account_id:
        raise WrongAccountError(
            "Refusing to scan: credentials belong to an account other than the "
            "approved sandbox. No IAM calls were made."
        )
    return actual


def list_all_users(iam_client):
    users = []
    for page in iam_client.get_paginator("list_users").paginate():
        users.extend(page["Users"])
    return users


def has_console_access(iam_client, user_name):
    """True if the user has a console password (a login profile)."""
    try:
        iam_client.get_login_profile(UserName=user_name)
        return True
    except iam_client.exceptions.NoSuchEntityException:
        return False


def list_mfa_serials(iam_client, user_name):
    """Serial numbers of every MFA device currently attached to the user."""
    serials = []
    for page in iam_client.get_paginator("list_mfa_devices").paginate(UserName=user_name):
        serials.extend(d["SerialNumber"] for d in page["MFADevices"])
    return serials


def collect(iam_client, sts_client, approved_account_id):
    """Build the snapshot dict. Raises on any error (fail closed)."""
    account_id = verify_account(sts_client, approved_account_id)

    users = []
    for u in list_all_users(iam_client):
        name = u["UserName"]
        users.append({
            "user_name": name,
            "created": u["CreateDate"].isoformat(),
            "console_access": has_console_access(iam_client, name),
            "mfa_devices": list_mfa_serials(iam_client, name),
        })

    return {
        "scan_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "account_id": account_id,
        "user_count": len(users),
        "users": users,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description="Read-only IAM MFA state collector")
    p.add_argument("--approved-account-id", required=True,
                   help="12-digit ID of the team's sandbox account")
    p.add_argument("--out", default="snapshot.json", help="snapshot output path")
    p.add_argument("--profile", help="optional AWS CLI profile name")
    args = p.parse_args(argv)

    session = boto3.Session(profile_name=args.profile) if args.profile else boto3.Session()
    try:
        snapshot = collect(session.client("iam"), session.client("sts"),
                           args.approved_account_id)
    except WrongAccountError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_WRONG_ACCOUNT
    except (ClientError, BotoCoreError) as e:
        print(f"ERROR: AWS call failed, no snapshot written: {e}", file=sys.stderr)
        return EXIT_AWS_ERROR

    with open(args.out, "w") as f:
        json.dump(snapshot, f, indent=2)
    print(f"Snapshot of {snapshot['user_count']} user(s) written to {args.out}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
