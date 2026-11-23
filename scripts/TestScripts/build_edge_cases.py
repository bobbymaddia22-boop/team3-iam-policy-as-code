#!/usr/bin/env python3
"""Build (or remove) the edge-case test users t6, t7, t8 in YOUR OWN practice AWS account.

    py build_edge_cases.py build   --profile team3-BobbyAWS
    py build_edge_cases.py cleanup --profile team3-BobbyAWS

Set APPROVED_ID to the account's 12 digits (no hyphens) first. The script refuses to run
in any other account. Passwords and MFA seeds are never printed or saved.
Needs: pip install boto3 pyotp

Cases (intended state is written to labeled-edge-cases.csv BEFORE each user is built):
  t6  console password and MFA were set, then the password was removed   -> NOT_APPLICABLE
  t7  console password, must reset at next sign-in, never used, no MFA  -> NON_COMPLIANT
  t8  username with + @ , and mixed case; console password, no MFA      -> NON_COMPLIANT
t9 (credential-report freshness) is not built here; it is a separate, optional test.
"""
import argparse, csv, os, secrets, sys, time
import boto3, pyotp
from botocore.exceptions import ClientError

TAG = [{"Key": "project", "Value": "team3-test"}]
T8_NAME = "t8.test+mfa,Case=A@team3"
# name, expected label, note
CASES = [
    ("t6", "NOT_APPLICABLE", "MFA device and password set, then password removed"),
    ("t7", "NON_COMPLIANT", "password with reset required, never used, no MFA"),
    (T8_NAME, "NON_COMPLIANT", "special characters in the name, password, no MFA"),
]
LABELS_FILE = "labeled-edge-cases.csv"


def code_of(err):
    return err.response["Error"]["Code"]


def retry(call, **kw):
    """IAM can lag right after create_user; retry NoSuchEntity a few times."""
    for attempt in range(6):
        try:
            return call(**kw)
        except ClientError as err:
            if code_of(err) != "NoSuchEntity" or attempt == 5:
                raise
            time.sleep(2)


def new_password():
    return secrets.token_urlsafe(24) + "aA1!"


def add_mfa(iam, user, device_name):
    dev = iam.create_virtual_mfa_device(VirtualMFADeviceName=device_name, Tags=TAG)["VirtualMFADevice"]
    totp = pyotp.TOTP(dev["Base32StringSeed"].decode())   # seed is never printed or saved
    now = time.time()
    retry(iam.enable_mfa_device, UserName=user, SerialNumber=dev["SerialNumber"],
          AuthenticationCode1=totp.at(now), AuthenticationCode2=totp.at(now + 30))
    return dev["SerialNumber"]


def exists(iam, name):
    try:
        iam.get_user(UserName=name)
        return True
    except ClientError as err:
        if code_of(err) != "NoSuchEntity":
            raise
        return False


def build(iam):
    for name, _, _ in CASES:
        if exists(iam, name):
            sys.exit(f"{name} already exists. Run 'cleanup' first.")
    with open(LABELS_FILE, "x", newline="") as fh:   # "x": never overwrite an earlier file
        out = csv.writer(fh)
        out.writerow(["user_name", "expected_status"])
        for name, label, note in CASES:
            out.writerow([name, label])   # write the intended state BEFORE building
            fh.flush()
            iam.create_user(UserName=name, Tags=TAG)
            if name == "t6":
                retry(iam.create_login_profile, UserName=name, Password=new_password())
                add_mfa(iam, name, "t6-mfa")
                iam.delete_login_profile(UserName=name)          # the point of the case
            elif name == "t7":
                retry(iam.create_login_profile, UserName=name, Password=new_password(),
                      PasswordResetRequired=True)
            else:
                retry(iam.create_login_profile, UserName=name, Password=new_password())
            print(f"built {name}: {note}")
    print(f"done; intended labels written to {LABELS_FILE}")


def cleanup(iam):
    for name, _, _ in CASES:
        try:
            tags = iam.list_user_tags(UserName=name)["Tags"]
        except ClientError as err:
            if code_of(err) == "NoSuchEntity":
                continue
            raise
        if {"Key": "project", "Value": "team3-test"} not in tags:
            print(f"skipping {name}: not tagged project=team3-test")
            continue
        for d in iam.list_mfa_devices(UserName=name)["MFADevices"]:
            iam.deactivate_mfa_device(UserName=name, SerialNumber=d["SerialNumber"])
            iam.delete_virtual_mfa_device(SerialNumber=d["SerialNumber"])
        try:
            iam.delete_login_profile(UserName=name)
        except ClientError as err:
            if code_of(err) != "NoSuchEntity":
                raise
        for k in iam.list_access_keys(UserName=name)["AccessKeyMetadata"]:
            iam.delete_access_key(UserName=name, AccessKeyId=k["AccessKeyId"])
        iam.delete_user(UserName=name)
        print("removed", name)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("action", choices=["build", "cleanup"])
    p.add_argument("--profile")
    a = p.parse_args()
    session = boto3.Session(profile_name=a.profile) if a.profile else boto3.Session()
    if session.client("sts").get_caller_identity()["Account"] != os.environ.get("APPROVED_ID"):
        sys.exit("Refusing to run: this is not the approved account (set APPROVED_ID).")
    iam = session.client("iam")
    try:
        (build if a.action == "build" else cleanup)(iam)
    except ClientError as err:
        info = err.response["Error"]
        sys.exit(f"STOPPED at {getattr(err, 'operation_name', '?')}: {info['Code']}: {info.get('Message', '')}\n"
                 "Some users may be half built; run 'cleanup' and try again.")


if __name__ == "__main__":
    main()
