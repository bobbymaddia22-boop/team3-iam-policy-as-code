#!/usr/bin/env python3
"""Check the IAM credential report for MFA coverage.

Read-only. Required IAM permissions:
  iam:GenerateCredentialReport, iam:GetCredentialReport
  (the account check uses sts:GetCallerIdentity, which needs no IAM permission)

Rule: every user with password_enabled = true must have mfa_active = true.
The root user's mfa_active value is reported separately and is not part of the
user-control result.

The raw credential report contains ARNs and timestamps, so this script does NOT
save it. It saves only a small, redacted summary.

Report age: AWS reuses a credential report that was generated within the last four
hours, so the report can be that old. The generation time AWS gives for the report is
recorded in the output as report_generated_utc, with report_age_minutes. Use
--max-report-age-minutes to refuse a report older than you can accept.

A report that is empty, cut off, missing its root row, or has values that are not
true/false is rejected with exit code 2. It is never scored as a pass.

Account safety: you must pass --approved-account-id. The script confirms the active
credentials belong to that account BEFORE any IAM call, and refuses otherwise.

Usage examples:
  py credential_report_check.py --approved-account-id 111122223333 --profile lab-readonly
  py credential_report_check.py --approved-account-id 111122223333 --max-report-age-minutes 30
  py credential_report_check.py --approved-account-id 111122223333 --show-names   # local use only!

Exit code: 0 = user control and root MFA both pass, 1 = at least one FAIL,
           2 = could not run (wrong account, AWS error, unusable or too-old report).
"""

import argparse
import csv
import io
import sys
import time
from datetime import datetime, timezone

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

ROOT = "<root_account>"
REQUIRED_COLUMNS = ("user", "password_enabled", "mfa_active")
TRUE_FALSE = ("true", "false")


class ReportError(Exception):
    """The credential report is empty, malformed, or incomplete."""


def parse_report(content):
    """Parse and validate the credential report. Raises ReportError if it cannot be trusted."""
    try:
        text = content.decode("utf-8-sig")
    except (UnicodeDecodeError, AttributeError):
        raise ReportError("the report content could not be decoded")
    if not text.strip():
        raise ReportError("the report is empty")

    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ReportError("the report is missing column(s): " + ", ".join(missing))

    rows = list(reader)
    if not rows:
        raise ReportError("the report has a header but no rows")

    for number, row in enumerate(rows, start=1):
        user = (row.get("user") or "").strip()
        if not user:
            raise ReportError(f"row {number} has no user name")
        mfa = (row.get("mfa_active") or "").strip().lower()
        if mfa not in TRUE_FALSE:
            raise ReportError(f"row {number} has an unexpected mfa_active value")
        if user != ROOT:
            password = (row.get("password_enabled") or "").strip().lower()
            if password not in TRUE_FALSE:
                raise ReportError(f"row {number} has an unexpected password_enabled value")

    if not any((r["user"] or "").strip() == ROOT for r in rows):
        raise ReportError("the report has no root account row")
    return rows


def fetch_report_rows(iam, timeout_seconds=60):
    """Ask AWS to generate the report, wait until it is ready, and parse it.

    Returns (rows, generated_time). generated_time is the time AWS gives for the report
    as a timezone-aware datetime, or None if AWS did not return one.
    """
    deadline = time.time() + timeout_seconds
    while True:
        state = iam.generate_credential_report()["State"]
        if state == "COMPLETE":
            break
        if time.time() > deadline:
            raise TimeoutError("Credential report was not ready in time. Try again.")
        time.sleep(2)

    response = iam.get_credential_report()
    rows = parse_report(response.get("Content", b""))
    generated = response.get("GeneratedTime")
    if generated is not None and generated.tzinfo is None:
        generated = generated.replace(tzinfo=timezone.utc)
    return rows, generated


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


def format_utc(moment):
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    parser = argparse.ArgumentParser(description="Check MFA coverage in the credential report.")
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
        "--max-report-age-minutes",
        type=int,
        help="Refuse a report older than this many minutes (exit code 2).",
    )
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
        report_rows, generated = fetch_report_rows(iam)
    except ClientError as err:
        code = err.response["Error"]["Code"]
        print(f"AWS error ({code}). Check that your profile has the read-only IAM "
              "permissions listed at the top of this script.", file=sys.stderr)
        return 2
    except TimeoutError as err:
        print(err, file=sys.stderr)
        return 2
    except ReportError as err:
        print(f"The credential report cannot be used: {err}. No result was produced.", file=sys.stderr)
        return 2

    age_minutes = None
    if generated is not None:
        age_minutes = max(0, round((datetime.now(timezone.utc) - generated).total_seconds() / 60))
    if args.max_report_age_minutes is not None:
        if age_minutes is None:
            print("AWS did not give a generation time for the report, so its age cannot be "
                  "checked. No result was produced.", file=sys.stderr)
            return 2
        if age_minutes > args.max_report_age_minutes:
            print(f"The credential report is {age_minutes} minutes old, older than the "
                  f"{args.max_report_age_minutes} minutes allowed. No result was produced.",
                  file=sys.stderr)
            return 2

    results = evaluate_rows(report_rows)
    root_rows = [r for r in results if r["user"] == ROOT]
    rows = [r for r in results if r["user"] != ROOT]
    if not rows:
        print("The report lists no IAM users, so nothing was checked. No result was produced.",
              file=sys.stderr)
        return 2

    root_ok = all(r["result"] == "PASS" for r in root_rows)

    if not args.show_names:
        rows = redact_names(rows)

    failures = [r for r in rows if r["result"] == "FAIL"]
    user_result = "FAIL" if failures else "PASS"
    root_result = "PASS" if root_ok else "FAIL"
    summary = {
        "checked_utc": utc_now_iso(),
        "account_id_masked": account_masked,
        "report_generated_utc": format_utc(generated) if generated is not None else None,
        "report_age_minutes": age_minutes,
        "user_control": {
            "users_checked": len(rows),
            "console_users": sum(1 for r in rows if r["console_access"] is True),
            "failures": len(failures),
            "result": user_result,
        },
        "root_mfa": {"enabled": root_ok, "result": root_result},
        "overall": "PASS" if user_result == "PASS" and root_result == "PASS" else "FAIL",
        "names_redacted": not args.show_names,
    }

    print_table(rows, ["user", "console_access", "mfa_active", "result"])
    print()
    print(f"Report generated: {summary['report_generated_utc'] or 'unknown'}"
          + (f" ({age_minutes} minutes old)" if age_minutes is not None else ""))
    print(f"User control: {user_result}  ({len(failures)} failing of "
          f"{summary['user_control']['console_users']} console user(s))")
    print(f"Root MFA (reported separately, not part of the user-control result): {root_result}")
    print(f"Overall: {summary['overall']}")

    for path in write_outputs(rows, summary, out_dir, "credential-report-mfa", args.format):
        print(f"Wrote {path}")

    return 0 if summary["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
