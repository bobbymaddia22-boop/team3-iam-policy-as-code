"""Shared helpers for the MFA configuration checks.

These scripts are READ-ONLY. They never create, change, or delete anything in AWS.
Credentials come from your AWS CLI profile or environment variables. Never put
keys in code.
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_client(service, profile=None):
    """Create a boto3 client using the named AWS CLI profile (or the default chain)."""
    try:
        import boto3
        from botocore.exceptions import ProfileNotFound
    except ImportError:
        sys.exit("boto3 is not installed. Run: pip install -r requirements.txt")
    try:
        session = boto3.Session(profile_name=profile)
    except ProfileNotFound:
        sys.exit(f"AWS profile '{profile}' was not found. Run 'aws configure list-profiles'.")
    return session.client(service)


def make_iam_client(profile=None):
    return _make_client("iam", profile)


def make_sts_client(profile=None):
    return _make_client("sts", profile)


class WrongAccountError(Exception):
    """The active credentials belong to an account other than the approved one."""


def account_id_arg(value):
    """argparse type: a 12-digit AWS account ID."""
    if not re.fullmatch(r"\d{12}", value):
        raise argparse.ArgumentTypeError("must be a 12-digit AWS account ID")
    return value


def mask_account_id(account_id):
    """Show only the last four digits, for example ********1234."""
    return "*" * 8 + str(account_id)[-4:]


def verify_account(sts, approved_account_id):
    """Refuse to continue unless the credentials belong to the approved account.

    Call this before any IAM call. It uses sts:GetCallerIdentity, which needs no IAM
    permission. Returns the masked account ID, which is safe to write to output.
    """
    actual = sts.get_caller_identity()["Account"]
    if actual != approved_account_id:
        raise WrongAccountError(
            f"Refusing to run: the active credentials are for account {mask_account_id(actual)}, "
            f"but the approved account is {mask_account_id(approved_account_id)}. "
            "Nothing was checked."
        )
    return mask_account_id(actual)


def redact_names(rows, key="user", keep=("<root_account>",)):
    """Replace real user names with user-001, user-002, ... (stable within one run)."""
    mapping = {}
    redacted = []
    for row in rows:
        name = row[key]
        if name not in keep and name not in mapping:
            mapping[name] = f"user-{len(mapping) + 1:03d}"
        new_row = dict(row)
        new_row[key] = name if name in keep else mapping[name]
        redacted.append(new_row)
    return redacted


def print_table(rows, columns):
    if not rows:
        print("(no rows)")
        return
    widths = {c: max(len(c), *(len(str(r[c])) for r in rows)) for c in columns}
    line = "  ".join(c.ljust(widths[c]) for c in columns)
    print(line)
    print("  ".join("-" * widths[c] for c in columns))
    for r in rows:
        print("  ".join(str(r[c]).ljust(widths[c]) for c in columns))


def write_outputs(rows, summary, out_dir, base_name, fmt):
    """Write results as JSON and/or CSV. Returns the list of files written."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    written = []

    if fmt in ("json", "both"):
        path = out_dir / f"{base_name}-{stamp}.json"
        payload = {"generated_utc": utc_now_iso(), "summary": summary, "results": rows}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        written.append(path)

    if fmt in ("csv", "both") and rows:
        path = out_dir / f"{base_name}-{stamp}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        written.append(path)

    return written
