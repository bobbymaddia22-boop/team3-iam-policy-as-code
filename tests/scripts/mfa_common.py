"""Shared helpers for the MFA enforcement checks.

These scripts are READ-ONLY. They never create, change, or delete anything in AWS.
Credentials come from your AWS CLI profile or environment variables. Never put
keys in code.
"""

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_iam_client(profile=None):
    """Create an IAM client using the named AWS CLI profile (or the default chain)."""
    try:
        import boto3
        from botocore.exceptions import ProfileNotFound
    except ImportError:
        sys.exit("boto3 is not installed. Run: pip install -r requirements.txt")
    try:
        session = boto3.Session(profile_name=profile)
    except ProfileNotFound:
        sys.exit(f"AWS profile '{profile}' was not found. Run 'aws configure list-profiles'.")
    return session.client("iam")


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
