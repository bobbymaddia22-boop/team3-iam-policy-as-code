"""Unit tests for scripts/credential_report_check.py.

No AWS account is used. IAM is replaced by a small fake client.

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
from pathlib import Path
from unittest import mock

from botocore.exceptions import ClientError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import credential_report_check as crc  # noqa: E402


def make_report(rows):
    """Build credential-report CSV bytes from (user, password_enabled, mfa_active) tuples."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["user", "password_enabled", "mfa_active"])
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


class FakeIam:
    def __init__(self, rows, states=("COMPLETE",), fail_generate=False):
        self.rows = rows
        self.states = list(states)
        self.fail_generate = fail_generate
        self.generate_calls = 0

    def generate_credential_report(self):
        self.generate_calls += 1
        if self.fail_generate:
            raise ClientError({"Error": {"Code": "AccessDenied", "Message": "no"}},
                              "GenerateCredentialReport")
        state = self.states.pop(0) if len(self.states) > 1 else self.states[0]
        return {"State": state}

    def get_credential_report(self):
        return {"Content": make_report(self.rows)}


GOOD = [("<root_account>", "not_supported", "true"), ("alice", "true", "true"),
        ("svc", "false", "false")]
BAD = [("<root_account>", "not_supported", "true"), ("alice", "true", "true"),
       ("mallory-real", "true", "false")]


def run_main(iam, *extra_args):
    out_dir = tempfile.mkdtemp()
    argv = ["credential_report_check.py", "--out-dir", out_dir, *extra_args]
    buffer = io.StringIO()
    with mock.patch.object(sys, "argv", argv), \
            mock.patch.object(crc, "make_iam_client", return_value=iam), \
            contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
        code = crc.main()
    return code, buffer.getvalue(), Path(out_dir)


class FetchReportTests(unittest.TestCase):
    def test_fetches_and_parses_report(self):
        rows = crc.fetch_report_rows(FakeIam(GOOD))
        self.assertEqual([r["user"] for r in rows], ["<root_account>", "alice", "svc"])
        self.assertEqual(rows[1]["mfa_active"], "true")

    def test_waits_until_report_is_complete(self):
        iam = FakeIam(GOOD, states=("STARTED", "INPROGRESS", "COMPLETE"))
        with mock.patch.object(crc.time, "sleep"):
            rows = crc.fetch_report_rows(iam)
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
        self.assertIn("<root_account>", written)

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
        self.assertEqual(data["summary"]["failures"], 1)
        self.assertEqual(data["summary"]["overall"], "FAIL")


if __name__ == "__main__":
    unittest.main()
