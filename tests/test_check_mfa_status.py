"""Unit tests for scripts/check_mfa_status.py and the helpers in scripts/mfa_common.py.

No AWS account is used. IAM and STS are replaced by small fake clients.

Run from the repository root:
    python -m unittest discover -s tests -v
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from botocore.exceptions import ClientError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_mfa_status as cms  # noqa: E402
import mfa_common  # noqa: E402


def client_error(code, operation):
    return ClientError({"Error": {"Code": code, "Message": code}}, operation)


class _Pages:
    def __init__(self, pages):
        self._pages = pages

    def paginate(self, **_kwargs):
        return iter(self._pages)


class FakeIam:
    """users: {name: (has_console_password, number_of_mfa_devices)}"""

    def __init__(self, users, root_mfa=1, fail_on=None):
        self.users = users
        self.root_mfa = root_mfa
        self.fail_on = fail_on

    def _maybe_fail(self, name):
        if self.fail_on == name:
            raise client_error("AccessDenied", name)

    def get_paginator(self, name):
        self._maybe_fail(name)
        if name == "list_users":
            names = list(self.users)
            pages = [{"Users": [{"UserName": n} for n in names[i:i + 2]]}
                     for i in range(0, len(names), 2)]
            return _Pages(pages or [{"Users": []}])
        if name == "list_mfa_devices":
            fake = self

            class DevicePages:
                def paginate(self, UserName):
                    count = fake.users[UserName][1]
                    devices = [{"SerialNumber": f"serial-{UserName}-{i}"} for i in range(count)]
                    # split into two pages to exercise pagination
                    return iter([{"MFADevices": devices[:1]}, {"MFADevices": devices[1:]}])

            return DevicePages()
        raise AssertionError(f"unexpected paginator: {name}")

    def get_login_profile(self, UserName):
        self._maybe_fail("get_login_profile")
        if not self.users[UserName][0]:
            raise client_error("NoSuchEntity", "GetLoginProfile")
        return {"LoginProfile": {"UserName": UserName}}

    def get_account_summary(self):
        self._maybe_fail("get_account_summary")
        return {"SummaryMap": {"AccountMFAEnabled": self.root_mfa}}


# The labeled lab users: t1 console+MFA, t2 console only, t3 no console,
# t4 console with MFA removed (no devices now), t5 console + two devices.
LABELED = {"t1": (True, 1), "t2": (True, 0), "t3": (False, 0), "t4": (True, 0), "t5": (True, 2)}


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


def run_main(iam, *extra_args, sts=None, approved=APPROVED):
    """Run main() with fake clients. Returns (exit_code, stdout, out_dir)."""
    out_dir = tempfile.mkdtemp()
    argv = ["check_mfa_status.py", "--out-dir", out_dir, *extra_args]
    if approved is not None:
        argv += ["--approved-account-id", approved]
    buffer = io.StringIO()
    with mock.patch.object(sys, "argv", argv), \
            mock.patch.object(cms, "make_iam_client", return_value=iam), \
            mock.patch.object(cms, "make_sts_client", return_value=sts or FakeSts()), \
            contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
        code = cms.main()
    return code, buffer.getvalue(), Path(out_dir)


class EvaluateTests(unittest.TestCase):
    def test_console_user_with_mfa_passes(self):
        self.assertEqual(cms.evaluate(True, 1), "PASS")

    def test_multiple_mfa_devices_pass(self):
        self.assertEqual(cms.evaluate(True, 2), "PASS")

    def test_console_user_without_mfa_fails(self):
        self.assertEqual(cms.evaluate(True, 0), "FAIL")

    def test_no_console_password_is_not_applicable(self):
        self.assertEqual(cms.evaluate(False, 0), "N/A")
        self.assertEqual(cms.evaluate(False, 1), "N/A")


class LoginProfileTests(unittest.TestCase):
    def test_existing_login_profile(self):
        iam = FakeIam({"alice": (True, 0)})
        self.assertTrue(cms.has_console_password(iam, "alice"))

    def test_missing_login_profile(self):
        iam = FakeIam({"svc": (False, 0)})
        self.assertFalse(cms.has_console_password(iam, "svc"))

    def test_other_aws_errors_are_not_swallowed(self):
        iam = FakeIam({"alice": (True, 0)}, fail_on="get_login_profile")
        with self.assertRaises(ClientError):
            cms.has_console_password(iam, "alice")


class DeviceCountTests(unittest.TestCase):
    def test_no_devices_returns_zero(self):
        self.assertEqual(cms.count_mfa_devices(FakeIam({"a": (True, 0)}), "a"), 0)

    def test_counts_devices_across_pages(self):
        self.assertEqual(cms.count_mfa_devices(FakeIam({"a": (True, 3)}), "a"), 3)


class CollectTests(unittest.TestCase):
    def test_labeled_users_get_expected_results(self):
        rows = {r["user"]: r["result"] for r in cms.collect_user_results(FakeIam(LABELED))}
        self.assertEqual(rows, {"t1": "PASS", "t2": "FAIL", "t3": "N/A", "t4": "FAIL", "t5": "PASS"})

    def test_users_across_pages_are_all_checked(self):
        self.assertEqual(len(cms.collect_user_results(FakeIam(LABELED))), 5)

    def test_empty_account_gives_no_rows(self):
        self.assertEqual(cms.collect_user_results(FakeIam({})), [])


class RootMfaTests(unittest.TestCase):
    def test_root_mfa_enabled(self):
        self.assertTrue(cms.root_mfa_enabled(FakeIam({}, root_mfa=1)))

    def test_root_mfa_disabled(self):
        self.assertFalse(cms.root_mfa_enabled(FakeIam({}, root_mfa=0)))

    def test_missing_summary_value_counts_as_disabled(self):
        iam = FakeIam({})
        iam.get_account_summary = lambda: {"SummaryMap": {}}
        self.assertFalse(cms.root_mfa_enabled(iam))


class MainTests(unittest.TestCase):
    def test_exit_0_when_everything_passes(self):
        code, _, _ = run_main(FakeIam({"t1": (True, 1), "t3": (False, 0)}))
        self.assertEqual(code, 0)

    def test_exit_1_when_a_console_user_has_no_mfa(self):
        code, out, _ = run_main(FakeIam(LABELED))
        self.assertEqual(code, 1)
        self.assertIn("FAIL", out)

    def test_exit_1_when_root_has_no_mfa(self):
        code, _, _ = run_main(FakeIam({"t1": (True, 1)}, root_mfa=0))
        self.assertEqual(code, 1)

    def test_exit_2_when_aws_denies_access(self):
        code, _, out_dir = run_main(FakeIam(LABELED, fail_on="list_users"))
        self.assertEqual(code, 2)
        self.assertEqual(list(out_dir.iterdir()), [])  # nothing written on failure

    def test_names_are_redacted_by_default(self):
        _, out, out_dir = run_main(FakeIam({"alice-real": (True, 0)}))
        written = "".join(p.read_text() for p in out_dir.iterdir())
        self.assertNotIn("alice-real", written)
        self.assertNotIn("alice-real", out)
        self.assertIn("user-001", written)

    def test_show_names_keeps_real_names(self):
        _, _, out_dir = run_main(FakeIam({"alice-real": (True, 0)}), "--show-names")
        written = "".join(p.read_text() for p in out_dir.iterdir())
        self.assertIn("alice-real", written)

    def test_summary_is_written_to_json(self):
        _, _, out_dir = run_main(FakeIam(LABELED))
        data = json.loads(next(out_dir.glob("*.json")).read_text())
        self.assertEqual(data["summary"]["user_control"]["failures"], 2)
        self.assertEqual(data["summary"]["user_control"]["result"], "FAIL")
        self.assertEqual(data["summary"]["overall"], "FAIL")


class AccountGuardTests(unittest.TestCase):
    def test_wrong_account_refuses_before_any_iam_call(self):
        code, _, out_dir = run_main(ExplodingIam(), sts=FakeSts(account=OTHER_ACCOUNT))
        self.assertEqual(code, 2)
        self.assertEqual(list(out_dir.iterdir()), [])

    def test_wrong_account_message_shows_only_last_four_digits(self):
        with self.assertRaises(mfa_common.WrongAccountError) as ctx:
            mfa_common.verify_account(FakeSts(account=OTHER_ACCOUNT), APPROVED)
        message = str(ctx.exception)
        self.assertNotIn(OTHER_ACCOUNT, message)
        self.assertNotIn(APPROVED, message)
        self.assertIn("9999", message)
        self.assertIn("3333", message)

    def test_sts_failure_refuses_before_any_iam_call(self):
        sts = FakeSts(error=client_error("ExpiredToken", "GetCallerIdentity"))
        code, _, out_dir = run_main(ExplodingIam(), sts=sts)
        self.assertEqual(code, 2)
        self.assertEqual(list(out_dir.iterdir()), [])

    def test_approved_account_id_is_required(self):
        with self.assertRaises(SystemExit) as ctx:
            run_main(ExplodingIam(), approved=None)
        self.assertEqual(ctx.exception.code, 2)

    def test_malformed_account_id_is_rejected(self):
        for bad in ("1234", "abcdefghijkl", "1111222233334"):
            with self.assertRaises(SystemExit):
                run_main(ExplodingIam(), approved=bad)

    def test_matching_account_runs_and_records_only_masked_id(self):
        code, out, out_dir = run_main(FakeIam({"t1": (True, 1)}))
        self.assertEqual(code, 0)
        written = "".join(p.read_text() for p in out_dir.iterdir())
        self.assertIn("********3333", written)
        self.assertNotIn(APPROVED, written + out)


class EmptyAndRootTests(unittest.TestCase):
    def test_no_users_is_not_a_success(self):
        code, _, out_dir = run_main(FakeIam({}))
        self.assertEqual(code, 2)
        self.assertEqual(list(out_dir.iterdir()), [])

    def test_root_result_is_separate_from_user_control(self):
        code, _, out_dir = run_main(FakeIam({"t1": (True, 1), "t3": (False, 0)}, root_mfa=0))
        summary = json.loads(next(out_dir.glob("*.json")).read_text())["summary"]
        self.assertEqual(summary["user_control"]["result"], "PASS")
        self.assertEqual(summary["user_control"]["failures"], 0)
        self.assertEqual(summary["root_mfa"], {"enabled": False, "result": "FAIL"})
        self.assertEqual(summary["overall"], "FAIL")
        self.assertEqual(code, 1)

    def test_root_is_not_counted_in_user_rows(self):
        _, _, out_dir = run_main(FakeIam(LABELED, root_mfa=0), "--format", "both")
        csv_text = next(out_dir.glob("*.csv")).read_text()
        self.assertNotIn("root", csv_text.lower())
        self.assertEqual(len(csv_text.strip().splitlines()), 6)  # header + 5 users


class AccountHelperTests(unittest.TestCase):
    def test_mask_account_id(self):
        self.assertEqual(mfa_common.mask_account_id("111122223333"), "********3333")

    def test_account_id_arg_accepts_twelve_digits(self):
        self.assertEqual(mfa_common.account_id_arg("111122223333"), "111122223333")

    def test_account_id_arg_rejects_other_input(self):
        import argparse
        for bad in ("", "123", "12345678901a", "1111222233334", " 111122223333"):
            with self.assertRaises(argparse.ArgumentTypeError):
                mfa_common.account_id_arg(bad)

    def test_verify_account_returns_masked_id(self):
        self.assertEqual(mfa_common.verify_account(FakeSts(), APPROVED), "********3333")


class CommonHelperTests(unittest.TestCase):
    def test_redact_names_is_stable_and_keeps_root(self):
        rows = [{"user": "<root_account>"}, {"user": "bob"}, {"user": "amy"}, {"user": "bob"}]
        names = [r["user"] for r in mfa_common.redact_names(rows)]
        self.assertEqual(names, ["<root_account>", "user-001", "user-002", "user-001"])

    def test_redact_names_does_not_change_the_input(self):
        rows = [{"user": "bob"}]
        mfa_common.redact_names(rows)
        self.assertEqual(rows[0]["user"], "bob")

    def test_write_outputs_creates_json_and_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = mfa_common.write_outputs([{"a": 1}], {"overall": "PASS"}, tmp, "t", "both")
            self.assertEqual(sorted(p.suffix for p in files), [".csv", ".json"])

    def test_utc_timestamp_format(self):
        stamp = mfa_common.utc_now_iso()
        self.assertRegex(stamp, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


if __name__ == "__main__":
    unittest.main()
