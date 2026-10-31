"""Unit tests for scripts/credential_report_check.py.

No AWS account is used. IAM and STS are replaced by small fake clients.

Run from the repository root:
    python -m unittest discover -s tests -v
"""

import contextlib
import csv
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from botocore.exceptions import ClientError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import credential_report_check as crc  # noqa: E402
import mfa_common  # noqa: E402


def make_report(rows):
    """Build credential-report CSV bytes from (user, password_enabled, mfa_active) tuples."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["user", "password_enabled", "mfa_active"])
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


class FakeIam:
    def __init__(self, rows, states=("COMPLETE",), fail_generate=False, content=None,
                 generated=None, include_generated=True):
        self.rows = rows
        self.states = list(states)
        self.fail_generate = fail_generate
        self.content = content
        self.generated = generated or (datetime.now(timezone.utc) - timedelta(minutes=5))
        self.include_generated = include_generated
        self.generate_calls = 0

    def generate_credential_report(self):
        self.generate_calls += 1
        if self.fail_generate:
            raise ClientError({"Error": {"Code": "AccessDenied", "Message": "no"}},
                              "GenerateCredentialReport")
        state = self.states.pop(0) if len(self.states) > 1 else self.states[0]
        return {"State": state}

    def get_credential_report(self):
        content = self.content if self.content is not None else make_report(self.rows)
        response = {"Content": content}
        if self.include_generated:
            response["GeneratedTime"] = self.generated
        return response


APPROVED = "111122223333"
OTHER_ACCOUNT = "999999999999"


class FakeSts:
    def __init__(self, account=APPROVED, error=None):
        self.account = account
        self.error = error

    def get_caller_identity(self):
        if self.error:
            raise self.error
        return {"Account": self.account}


class ExplodingIam:
    """Any use fails the test. Proves that no IAM call happened."""

    def __getattr__(self, name):
        raise AssertionError(f"IAM must not be called, but .{name} was used")


GOOD = [("<root_account>", "not_supported", "true"), ("alice", "true", "true"),
        ("svc", "false", "false")]
BAD = [("<root_account>", "not_supported", "true"), ("alice", "true", "true"),
       ("mallory-real", "true", "false")]


def run_main(iam, *extra_args, sts=None, approved=APPROVED):
    out_dir = tempfile.mkdtemp()
    argv = ["credential_report_check.py", "--out-dir", out_dir, *extra_args]
    if approved is not None:
        argv += ["--approved-account-id", approved]
    buffer = io.StringIO()
    with mock.patch.object(sys, "argv", argv), \
            mock.patch.object(crc, "make_iam_client", return_value=iam), \
            mock.patch.object(crc, "make_sts_client", return_value=sts or FakeSts()), \
            contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
        code = crc.main()
    return code, buffer.getvalue(), Path(out_dir)


class FetchReportTests(unittest.TestCase):
    def test_fetches_and_parses_report(self):
        rows, _ = crc.fetch_report_rows(FakeIam(GOOD))
        self.assertEqual([r["user"] for r in rows], ["<root_account>", "alice", "svc"])
        self.assertEqual(rows[1]["mfa_active"], "true")

    def test_waits_until_report_is_complete(self):
        iam = FakeIam(GOOD, states=("STARTED", "INPROGRESS", "COMPLETE"))
        with mock.patch.object(crc.time, "sleep"):
            rows, _ = crc.fetch_report_rows(iam)
        self.assertEqual(iam.generate_calls, 3)
        self.assertEqual(len(rows), 3)

    def test_times_out_if_report_never_completes(self):
        iam = FakeIam(GOOD, states=("STARTED",))
        clock = iter([0, 1, 100, 200])
        with mock.patch.object(crc.time, "sleep"), \
                mock.patch.object(crc.time, "time", side_effect=lambda: next(clock)):
            with self.assertRaises(TimeoutError):
                crc.fetch_report_rows(iam, timeout_seconds=10)

    def test_aws_errors_are_propagated(self):
        with self.assertRaises(ClientError):
            crc.fetch_report_rows(FakeIam(GOOD, fail_generate=True))


class EvaluateRowsTests(unittest.TestCase):
    def evaluate(self, rows):
        parsed = list(csv.DictReader(io.StringIO(make_report(rows).decode())))
        return {r["user"]: r["result"] for r in crc.evaluate_rows(parsed)}

    def test_root_user_with_mfa_passes(self):
        self.assertEqual(self.evaluate([("<root_account>", "not_supported", "true")]),
                         {"<root_account>": "PASS"})

    def test_root_user_without_mfa_fails(self):
        self.assertEqual(self.evaluate([("<root_account>", "not_supported", "false")]),
                         {"<root_account>": "FAIL"})

    def test_console_user_with_mfa_passes(self):
        self.assertEqual(self.evaluate([("alice", "true", "true")]), {"alice": "PASS"})

    def test_console_user_without_mfa_fails(self):
        self.assertEqual(self.evaluate([("mallory-real", "true", "false")]), {"mallory-real": "FAIL"})

    def test_user_without_console_password_is_not_applicable(self):
        self.assertEqual(self.evaluate([("svc", "false", "false")]), {"svc": "N/A"})

    def test_values_are_case_insensitive(self):
        self.assertEqual(self.evaluate([("alice", "TRUE", "True")]), {"alice": "PASS"})


class ReportValidationTests(unittest.TestCase):
    def assert_rejected(self, content, fragment):
        with self.assertRaises(crc.ReportError) as ctx:
            crc.parse_report(content)
        self.assertIn(fragment, str(ctx.exception))

    def test_valid_report_is_accepted(self):
        self.assertEqual(len(crc.parse_report(make_report(GOOD))), 3)

    def test_empty_report_is_rejected(self):
        self.assert_rejected(b"", "empty")

    def test_whitespace_only_report_is_rejected(self):
        self.assert_rejected(b"  \n \n", "empty")

    def test_header_only_report_is_rejected(self):
        self.assert_rejected(b"user,password_enabled,mfa_active\n", "no rows")

    def test_missing_column_is_rejected(self):
        self.assert_rejected(b"user,password_enabled\nalice,true\n", "mfa_active")

    def test_report_without_root_row_is_rejected(self):
        self.assert_rejected(make_report([("alice", "true", "true")]), "root")

    def test_unexpected_mfa_value_is_rejected(self):
        self.assert_rejected(make_report([("<root_account>", "not_supported", "true"),
                                          ("alice", "true", "maybe")]), "mfa_active")

    def test_unexpected_password_value_is_rejected(self):
        self.assert_rejected(make_report([("<root_account>", "not_supported", "true"),
                                          ("alice", "N/A", "true")]), "password_enabled")

    def test_cut_off_row_is_rejected(self):
        self.assert_rejected(b"user,password_enabled,mfa_active\n<root_account>,not_supported,true\nalice,true\n",
                             "mfa_active")

    def test_row_without_user_name_is_rejected(self):
        self.assert_rejected(make_report([("<root_account>", "not_supported", "true"),
                                          ("", "true", "true")]), "no user name")

    def test_undecodable_content_is_rejected(self):
        self.assert_rejected(b"\xff\xfe\x00bad", "decoded")


class GeneratedTimeTests(unittest.TestCase):
    def test_generated_time_is_returned(self):
        moment = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
        _, generated = crc.fetch_report_rows(FakeIam(GOOD, generated=moment))
        self.assertEqual(generated, moment)

    def test_naive_generated_time_is_treated_as_utc(self):
        _, generated = crc.fetch_report_rows(FakeIam(GOOD, generated=datetime(2026, 10, 31, 12, 0)))
        self.assertEqual(generated.tzinfo, timezone.utc)

    def test_missing_generated_time_gives_none(self):
        _, generated = crc.fetch_report_rows(FakeIam(GOOD, include_generated=False))
        self.assertIsNone(generated)

    def test_generation_time_and_age_are_written_to_the_summary(self):
        moment = datetime.now(timezone.utc) - timedelta(minutes=42)
        _, _, out_dir = run_main(FakeIam(GOOD, generated=moment))
        summary = json.loads(next(out_dir.glob("*.json")).read_text())["summary"]
        self.assertEqual(summary["report_generated_utc"], moment.strftime("%Y-%m-%dT%H:%M:%SZ"))
        self.assertIn(summary["report_age_minutes"], (41, 42, 43))

    def test_unknown_generation_time_is_recorded_as_null(self):
        _, _, out_dir = run_main(FakeIam(GOOD, include_generated=False))
        summary = json.loads(next(out_dir.glob("*.json")).read_text())["summary"]
        self.assertIsNone(summary["report_generated_utc"])
        self.assertIsNone(summary["report_age_minutes"])

    def test_report_older_than_the_limit_is_refused(self):
        old = datetime.now(timezone.utc) - timedelta(minutes=200)
        code, _, out_dir = run_main(FakeIam(GOOD, generated=old), "--max-report-age-minutes", "60")
        self.assertEqual(code, 2)
        self.assertEqual(list(out_dir.iterdir()), [])

    def test_report_within_the_limit_is_accepted(self):
        code, _, _ = run_main(FakeIam(GOOD), "--max-report-age-minutes", "60")
        self.assertEqual(code, 0)

    def test_age_limit_with_unknown_generation_time_is_refused(self):
        code, _, _ = run_main(FakeIam(GOOD, include_generated=False), "--max-report-age-minutes", "60")
        self.assertEqual(code, 2)


class GuardAndInputTests(unittest.TestCase):
    def test_wrong_account_refuses_before_any_iam_call(self):
        code, _, out_dir = run_main(ExplodingIam(), sts=FakeSts(account=OTHER_ACCOUNT))
        self.assertEqual(code, 2)
        self.assertEqual(list(out_dir.iterdir()), [])

    def test_sts_failure_refuses_before_any_iam_call(self):
        sts = FakeSts(error=ClientError({"Error": {"Code": "ExpiredToken", "Message": "x"}},
                                        "GetCallerIdentity"))
        code, _, _ = run_main(ExplodingIam(), sts=sts)
        self.assertEqual(code, 2)

    def test_approved_account_id_is_required(self):
        with self.assertRaises(SystemExit) as ctx:
            run_main(ExplodingIam(), approved=None)
        self.assertEqual(ctx.exception.code, 2)

    def test_only_the_masked_account_id_is_written(self):
        _, out, out_dir = run_main(FakeIam(GOOD))
        written = "".join(p.read_text() for p in out_dir.iterdir())
        self.assertIn("********3333", written)
        self.assertNotIn(APPROVED, written + out)

    def test_empty_report_is_not_a_success(self):
        code, _, out_dir = run_main(FakeIam([], content=b""))
        self.assertEqual(code, 2)
        self.assertEqual(list(out_dir.iterdir()), [])

    def test_header_only_report_is_not_a_success(self):
        code, _, out_dir = run_main(FakeIam([], content=b"user,password_enabled,mfa_active\n"))
        self.assertEqual(code, 2)
        self.assertEqual(list(out_dir.iterdir()), [])

    def test_report_with_only_the_root_row_is_not_a_success(self):
        code, _, out_dir = run_main(FakeIam([("<root_account>", "not_supported", "true")]))
        self.assertEqual(code, 2)
        self.assertEqual(list(out_dir.iterdir()), [])


class RootSeparationTests(unittest.TestCase):
    ROOT_OFF = [("<root_account>", "not_supported", "false"), ("alice", "true", "true")]

    def test_root_failure_does_not_change_the_user_control_result(self):
        code, _, out_dir = run_main(FakeIam(self.ROOT_OFF))
        summary = json.loads(next(out_dir.glob("*.json")).read_text())["summary"]
        self.assertEqual(summary["user_control"]["result"], "PASS")
        self.assertEqual(summary["user_control"]["failures"], 0)
        self.assertEqual(summary["root_mfa"], {"enabled": False, "result": "FAIL"})
        self.assertEqual(summary["overall"], "FAIL")
        self.assertEqual(code, 1)

    def test_root_row_is_not_in_the_user_rows(self):
        _, _, out_dir = run_main(FakeIam(GOOD), "--format", "both")
        rows_csv = next(out_dir.glob("*.csv")).read_text()
        self.assertNotIn("root", rows_csv.lower())
        data = json.loads(next(out_dir.glob("*.json")).read_text())
        self.assertEqual([r["user"] for r in data["results"]], ["user-001", "user-002"])
        self.assertEqual(data["summary"]["user_control"]["users_checked"], 2)


class MainTests(unittest.TestCase):
    def test_exit_0_when_all_pass(self):
        code, _, _ = run_main(FakeIam(GOOD))
        self.assertEqual(code, 0)

    def test_exit_1_when_a_console_user_has_no_mfa(self):
        code, out, _ = run_main(FakeIam(BAD))
        self.assertEqual(code, 1)
        self.assertIn("FAIL", out)

    def test_exit_2_when_aws_denies_access(self):
        code, _, out_dir = run_main(FakeIam(GOOD, fail_generate=True))
        self.assertEqual(code, 2)
        self.assertEqual(list(out_dir.iterdir()), [])

    def test_names_are_redacted_by_default(self):
        _, out, out_dir = run_main(FakeIam(BAD))
        written = "".join(p.read_text() for p in out_dir.iterdir())
        # Ignore the "Wrote <path>" line: a local temp path can contain any text.
        shown = "\n".join(line for line in out.splitlines() if not line.startswith("Wrote "))
        self.assertNotIn("mallory-real", written + shown)
        self.assertIn("root_mfa", written)

    def test_show_names_keeps_real_names(self):
        _, _, out_dir = run_main(FakeIam(BAD), "--show-names")
        self.assertIn("mallory-real", "".join(p.read_text() for p in out_dir.iterdir()))

    def test_raw_report_is_never_saved(self):
        _, _, out_dir = run_main(FakeIam(BAD), "--format", "both")
        for path in out_dir.iterdir():
            self.assertNotIn("password_enabled", path.read_text())

    def test_summary_counts_failures(self):
        _, _, out_dir = run_main(FakeIam(BAD))
        data = json.loads(next(out_dir.glob("*.json")).read_text())
        self.assertEqual(data["summary"]["user_control"]["failures"], 1)
        self.assertEqual(data["summary"]["user_control"]["result"], "FAIL")
        self.assertEqual(data["summary"]["overall"], "FAIL")


if __name__ == "__main__":
    unittest.main()
