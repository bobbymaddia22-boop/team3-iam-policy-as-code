#!/usr/bin/env python3
"""Build (or remove) the five labeled test users t1-t5 in YOUR OWN practice AWS account.

    py build_t1_t5.py build   --profile my-sandbox
    py build_t1_t5.py cleanup --profile my-sandbox

Set APPROVED_ID to your practice account's 12 digits (no hyphens) first:
    PowerShell:  $env:APPROVED_ID = "123456789012"
The script refuses to run in any other account. Passwords, access-key secrets and MFA
seeds are never printed or saved. Needs: pip install boto3 pyotp
Writes labeled-population.csv (same format as evidence/run-01/labeled-population.csv).
"""
import argparse, csv, os, secrets, sys, time
import boto3, pyotp
from botocore.exceptions import ClientError

TAG = [{"Key": "project", "Value": "team3-test"}]
# name, console password?, MFA devices to END with, extra steps
USERS = [
    ("t1", True, 1, "one MFA device"),
    ("t2", True, 0, "no MFA device"),
    ("t3", False, 0, "no console password; access key only"),
    ("t4", True, 0, "MFA device added, then removed"),
    ("t5", True, 2, "two MFA devices"),
]
EXPECTED = lambda pw, devs: "NOT_APPLICABLE" if not pw else ("COMPLIANT" if devs else "NON_COMPLIANT")


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


def add_mfa(iam, user, device_name):
    dev = iam.create_virtual_mfa_device(VirtualMFADeviceName=device_name, Tags=TAG)["VirtualMFADevice"]
    totp = pyotp.TOTP(dev["Base32StringSeed"].decode())   # seed is never printed or saved
    now = time.time()
    retry(iam.enable_mfa_device, UserName=user, SerialNumber=dev["SerialNumber"],
          AuthenticationCode1=totp.at(now), AuthenticationCode2=totp.at(now + 30))
    return dev["SerialNumber"]


def build(iam):
    for name, *_ in USERS:   # refuse to touch anything that already exists
        try:
            iam.get_user(UserName=name)
            sys.exit(f"{name} already exists. Run 'cleanup' first (or pick a clean account).")
        except ClientError as err:
            if code_of(err) != "NoSuchEntity":
                raise
    with open("labeled-population.csv", "w", newline="") as fh:
        out = csv.writer(fh)
        out.writerow(["user_name", "console_password", "mfa_devices", "expected_status"])
        for name, pw, devs, note in USERS:
            out.writerow([name, "yes" if pw else "no", devs, EXPECTED(pw, devs)])
    for name, pw, devs, note in USERS:
        iam.create_user(UserName=name, Tags=TAG)
        if pw:
            retry(iam.create_login_profile, UserName=name, Password=secrets.token_urlsafe(24) + "aA1!")
        if name == "t1":
            add_mfa(iam, name, "t1-mfa")
        elif name == "t3":
            retry(iam.create_access_key, UserName=name)   # secret is discarded, never saved
        elif name == "t4":
            serial = add_mfa(iam, name, "t4-mfa")          # added...
            iam.deactivate_mfa_device(UserName=name, SerialNumber=serial)   # ...then removed
            iam.delete_virtual_mfa_device(SerialNumber=serial)
        elif name == "t5":
            add_mfa(iam, name, "t5-mfa-a")
            add_mfa(iam, name, "t5-mfa-b")
        print(f"built {name}: {note}")
    print("done; answer key written to labeled-population.csv")


def cleanup(iam):
    for name, *_ in USERS:
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
