#!/usr/bin/env python3
"""
Automated MFA check: collector -> OPA policy -> report
-------------------------------------------------------
Team 3 - Cloud Identity and Policy-as-Code Assurance

Runs the whole automated path in one command and records how long each stage
took, so the run can be compared with the manual audit.

    python run_check.py --approved-account-id 123456789012 --outdir evidence/run1

Outputs in --outdir:
    snapshot.json   raw IAM facts (private; contains the full account ID)
    report.json     OPA decision per user, timestamp, account ID, timings
    report.csv      one row per user for scoring against ground truth

Requires the `opa` binary (set --opa or the OPA_BIN environment variable if it
is not on PATH).
"""

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

import collect_iam_state as collector

HERE = Path(__file__).resolve().parent
EXIT_OPA_ERROR = 4


def mask(account_id):
    """Keep only the last four digits (for public evidence)."""
    return "*" * (len(account_id) - 4) + account_id[-4:]


def evaluate_with_opa(opa_bin, snapshot_path, policy_dir):
    """Run `opa eval` on the snapshot and return the report object."""
    cmd = [opa_bin, "eval", "--format", "json",
           "--input", str(snapshot_path), "--data", str(policy_dir),
           "data.mfa.report"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"opa eval failed: {proc.stderr.strip() or proc.stdout.strip()}")
    result = json.loads(proc.stdout)["result"]
    if not result:
        raise RuntimeError("opa returned no result; policy or input is invalid")
    return result[0]["expressions"][0]["value"]


def run(iam_client, sts_client, approved_account_id, outdir, opa_bin,
        policy_dir=HERE / "policy", mask_account_id=False):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    snapshot = collector.collect(iam_client, sts_client, approved_account_id)
    t1 = time.perf_counter()

    snapshot_path = outdir / "snapshot.json"
    snapshot_path.write_text(json.dumps(snapshot, indent=2))

    decision = evaluate_with_opa(opa_bin, snapshot_path, policy_dir)
    t2 = time.perf_counter()

    shown_id = mask(snapshot["account_id"]) if mask_account_id else snapshot["account_id"]
    by_name = {u["user_name"]: u for u in snapshot["users"]}

    rows = []
    for name in sorted(decision["user_status"]):
        u = by_name[name]
        rows.append({
            "user_name": name,
            "console_access": u["console_access"],
            "mfa_device_count": len(u["mfa_devices"]),
            "status": decision["user_status"][name],
        })

    report = {
        "scan_timestamp_utc": snapshot["scan_timestamp_utc"],
        "account_id": shown_id,
        "total_users": decision["total_users"],
        "noncompliant_count": decision["noncompliant_count"],
        "noncompliant_users": decision["noncompliant_users"],
        "results": rows,
        "timing_seconds": {
            "collect": round(t1 - t0, 4),
            "evaluate": round(t2 - t1, 4),
            "total": round(t2 - t0, 4),
        },
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    with open(outdir / "report.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["user_name", "console_access",
                                          "mfa_device_count", "status"])
        w.writeheader()
        w.writerows(rows)
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description="Collector + OPA MFA check")
    p.add_argument("--approved-account-id", required=True)
    p.add_argument("--outdir", default="evidence/run")
    p.add_argument("--profile")
    p.add_argument("--opa", default=os.environ.get("OPA_BIN") or shutil.which("opa"))
    p.add_argument("--mask-account-id", action="store_true",
                   help="show only the last 4 digits in report files")
    args = p.parse_args(argv)

    if not args.opa:
        print("ERROR: opa binary not found; use --opa or set OPA_BIN", file=sys.stderr)
        return EXIT_OPA_ERROR

    session = boto3.Session(profile_name=args.profile) if args.profile else boto3.Session()
    try:
        report = run(session.client("iam"), session.client("sts"),
                     args.approved_account_id, args.outdir, args.opa,
                     mask_account_id=args.mask_account_id)
    except collector.WrongAccountError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return collector.EXIT_WRONG_ACCOUNT
    except (ClientError, BotoCoreError) as e:
        print(f"ERROR: AWS call failed, no report written: {e}", file=sys.stderr)
        return collector.EXIT_AWS_ERROR
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_OPA_ERROR

    print(f"Scanned {report['total_users']} user(s); "
          f"{report['noncompliant_count']} noncompliant: {report['noncompliant_users']}")
    print(f"Total time {report['timing_seconds']['total']} s; reports in {args.outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
