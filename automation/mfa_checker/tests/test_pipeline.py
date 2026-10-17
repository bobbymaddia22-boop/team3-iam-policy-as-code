"""
End-to-end tests for the collector + OPA pipeline, run against a SIMULATED
IAM service (moto). Nothing here touches a real AWS account.

    pytest -v tests/

Needs the `opa` binary: set OPA_BIN or put it on PATH.
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import collect_iam_state as collector  # noqa: E402
import run_check  # noqa: E402

SANDBOX_ID = "123456789012"  # moto's default simulated account

# Ground truth: the labeled test cases from Report 1, Section 4.
# Positive class = NON_COMPLIANT.
GROUND_TRUTH = {
    "t1": "COMPLIANT",
    "t2": "NON_COMPLIANT",
    "t3": "NOT_APPLICABLE",
    "t4": "NON_COMPLIANT",
    "t5": "COMPLIANT",
}


@pytest.fixture(scope="module")
def opa_bin():
    path = os.environ.get("OPA_BIN") or shutil.which("opa") or "/tmp/opa"
    if not Path(path).exists():
        pytest.skip("opa binary not found; set OPA_BIN")
    return path


@pytest.fixture(autouse=True)
def fake_aws_env(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


def add_mfa(iam, user, label):
    dev = iam.create_virtual_mfa_device(VirtualMFADeviceName=f"{user}-{label}")
    serial = dev["VirtualMFADevice"]["SerialNumber"]
    iam.enable_mfa_device(UserName=user, SerialNumber=serial,
                          AuthenticationCode1="123456", AuthenticationCode2="654321")
    return serial


def build_labeled_environment(iam):
    for name in GROUND_TRUTH:
        iam.create_user(UserName=name)
    # T1: console + one MFA device
    iam.create_login_profile(UserName="t1", Password="Sample-Pass-1!")
    add_mfa(iam, "t1", "a")
    # T2: console, no MFA
    iam.create_login_profile(UserName="t2", Password="Sample-Pass-2!")
    # T3: access key only, no console password, no MFA
    iam.create_access_key(UserName="t3")
    # T4: console, MFA registered then deactivated
    iam.create_login_profile(UserName="t4", Password="Sample-Pass-4!")
    serial = add_mfa(iam, "t4", "a")
    iam.deactivate_mfa_device(UserName="t4", SerialNumber=serial)
    # T5: console, two MFA devices
    iam.create_login_profile(UserName="t5", Password="Sample-Pass-5!")
    add_mfa(iam, "t5", "a")
    add_mfa(iam, "t5", "b")


def clients():
    return boto3.client("iam"), boto3.client("sts")


def score(report):
    """Confusion matrix with NON_COMPLIANT as the positive class."""
    tp = fp = fn = tn = 0
    for row in report["results"]:
        predicted = row["status"] == "NON_COMPLIANT"
        actual = GROUND_TRUTH[row["user_name"]] == "NON_COMPLIANT"
        tp += predicted and actual
        fp += predicted and not actual
        fn += (not predicted) and actual
        tn += (not predicted) and not actual
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


@mock_aws
def test_labeled_environment_matches_ground_truth(tmp_path, opa_bin):
    iam, sts = clients()
    build_labeled_environment(iam)
    report = run_check.run(iam, sts, SANDBOX_ID, tmp_path, opa_bin)

    got = {r["user_name"]: r["status"] for r in report["results"]}
    assert got == GROUND_TRUTH
    assert report["noncompliant_users"] == ["t2", "t4"]
    assert score(report) == {"tp": 2, "fp": 0, "fn": 0, "tn": 3}


@mock_aws
def test_report_records_timestamp_account_and_timing(tmp_path, opa_bin):
    iam, sts = clients()
    build_labeled_environment(iam)
    report = run_check.run(iam, sts, SANDBOX_ID, tmp_path, opa_bin)

    ts = datetime.fromisoformat(report["scan_timestamp_utc"])
    assert ts.utcoffset().total_seconds() == 0  # UTC (SR4)
    assert report["account_id"] == SANDBOX_ID  # SR4
    assert set(report["timing_seconds"]) == {"collect", "evaluate", "total"}
    assert (tmp_path / "report.json").exists() and (tmp_path / "report.csv").exists()


@mock_aws
def test_wrong_account_is_refused_before_any_iam_call(tmp_path, opa_bin):
    """SR3: unapproved account -> abort, no IAM calls, nothing written."""
    class ExplodingIam:
        def __getattr__(self, name):
            raise AssertionError(f"IAM call attempted: {name}")

    _, sts = clients()
    with pytest.raises(collector.WrongAccountError):
        run_check.run(ExplodingIam(), sts, "999999999999", tmp_path, opa_bin)
    assert not (tmp_path / "report.json").exists()
    assert not (tmp_path / "snapshot.json").exists()


@mock_aws
def test_cli_exit_code_for_wrong_account(tmp_path):
    out = tmp_path / "snap.json"
    code = collector.main(["--approved-account-id", "999999999999", "--out", str(out)])
    assert code == collector.EXIT_WRONG_ACCOUNT
    assert not out.exists()


@mock_aws
def test_missing_permission_fails_closed(tmp_path, opa_bin):
    """A denied IAM call must abort with no report, never a clean-looking one."""
    iam, sts = clients()
    build_labeled_environment(iam)

    class DeniedMfaListing:
        def __init__(self, real):
            self._real = real
            self.exceptions = real.exceptions

        def get_paginator(self, op):
            if op == "list_mfa_devices":
                raise ClientError({"Error": {"Code": "AccessDenied", "Message": "denied"}},
                                  "ListMFADevices")
            return self._real.get_paginator(op)

        def __getattr__(self, name):
            return getattr(self._real, name)

    with pytest.raises(ClientError):
        run_check.run(DeniedMfaListing(iam), sts, SANDBOX_ID, tmp_path, opa_bin)
    assert not (tmp_path / "report.json").exists()
    assert not (tmp_path / "report.csv").exists()


@mock_aws
def test_empty_account_gives_valid_empty_report(tmp_path, opa_bin):
    iam, sts = clients()
    report = run_check.run(iam, sts, SANDBOX_ID, tmp_path, opa_bin)
    assert report["total_users"] == 0
    assert report["noncompliant_users"] == []
    assert json.loads((tmp_path / "report.json").read_text())["results"] == []


@mock_aws
def test_masked_report_hides_account_id_but_snapshot_keeps_it(tmp_path, opa_bin):
    iam, sts = clients()
    build_labeled_environment(iam)
    report = run_check.run(iam, sts, SANDBOX_ID, tmp_path, opa_bin, mask_account_id=True)
    assert report["account_id"] == "********9012"
    assert SANDBOX_ID not in (tmp_path / "report.json").read_text()
    assert json.loads((tmp_path / "snapshot.json").read_text())["account_id"] == SANDBOX_ID


@mock_aws
def test_collector_issues_only_read_only_calls():
    """SR2: the collector must not use any create/delete/update/attach call."""
    iam, sts = clients()
    build_labeled_environment(iam)

    seen = []

    class Recorder:
        def __init__(self, real):
            self._real = real
            self.exceptions = real.exceptions

        def get_paginator(self, op):
            seen.append(op)
            return self._real.get_paginator(op)

        def __getattr__(self, name):
            attr = getattr(self._real, name)
            if callable(attr):
                seen.append(name)
            return attr

    collector.collect(Recorder(iam), sts, SANDBOX_ID)
    allowed = {"list_users", "list_mfa_devices", "get_login_profile"}
    assert set(seen) <= allowed, f"unexpected calls: {set(seen) - allowed}"
