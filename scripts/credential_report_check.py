#!/usr/bin/env python3
"""Check the IAM credential report for MFA coverage. (Test cases MFA-06/07)

Read-only. Required IAM permissions:
  iam:GenerateCredentialReport, iam:GetCredentialReport

Rule: every user with password_enabled = true must have mfa_active = true.
The root user's mfa_active value is reported separately.

The raw credential report contains ARNs and timestamps, so this script does NOT
save it. It saves only a small, redacted summary.

Usage examples:
  python credential_report_check.py --profile lab-readonly
  python credential_report_check.py --profile lab-readonly --format both
  python credential_report_check.py --profile lab-readonly --show-names   # local use only!

Exit code: 0 = all checks pass, 1 = at least one FAIL, 2 = could not run.
"""

import argparse
import csv
import io
import sys
import time

from botocore.exceptions import ClientError

from mfa_common import make_iam_client, print_table, redact_names, utc_now_iso, write_outputs

ROOT = "<root_account>"


def fetch_report_rows(iam, timeout_seconds=60):
    """Ask AWS to generate the report, wait until it is ready, and parse it."""
    deadline = time.time() + timeout_seconds
    while True:
        state = iam.generate_credential_report()["State"]
        if state == "COMPLETE":
            break
        if time.time() > deadline:
            raise TimeoutError("Credential report was not ready in time. Try again.")
        time.sleep(2)

    content = iam.get_credential_report()["Content"].decode("utf-8")
    return list(csv.DictReader(io.StringIO(content)))


def evaluate_rows(report_rows):
    results = []
    for row in report_rows:
        user = row["user"]
        mfa_active = row["mfa_active"].strip().lower() == "true"
        if user == ROOT:
            result = "PASS" if mfa_active else "FAIL"
            console = "n/a"
        else:
            console = row["password_enabled"].strip().lower() == "true"
            if not console:
                result = "N/A"
            else:
                result = "PASS" if mfa_active else "FAIL"
        results.append(
            {"user": user, "console_access": console, "mfa_active": mfa_active, "result": result}
        )
    return results


def main():
    parser = argparse.ArgumentParser(description="Check MFA coverage in the credential report.")
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
        rows = evaluate_rows(fetch_report_rows(iam))
    except ClientError as err:
        code = err.response["Error"]["Code"]
        print(f"AWS error ({code}). Check that your profile has the read-only IAM "
              "permissions listed at the top of this script.", file=sys.stderr)
        return 2
    except TimeoutError as err:
        print(err, file=sys.stderr)
        return 2

    if not args.show_names:
        rows = redact_names(rows)

    failures = [r for r in rows if r["result"] == "FAIL"]
    summary = {
        "checked_utc": utc_now_iso(),
        "rows_checked": len(rows),
        "failures": len(failures),
        "overall": "PASS" if not failures else "FAIL",
        "names_redacted": not args.show_names,
    }

    print_table(rows, ["user", "console_access", "mfa_active", "result"])
    print()
    print(f"Overall: {summary['overall']}  ({len(failures)} failing row(s))")

    for path in write_outputs(rows, summary, out_dir, "credential-report-mfa", args.format):
        print(f"Wrote {path}")

    return 0 if summary["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
