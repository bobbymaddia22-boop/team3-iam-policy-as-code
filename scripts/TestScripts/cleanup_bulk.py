#!/usr/bin/env python3
"""Remove the bulk test users t<FIRST>..t<FIRST+COUNT-1> from YOUR OWN practice account.

    py cleanup_bulk.py --first 10 --count 3  --profile team3-BobbyAWS    # pilot t10-t12
    py cleanup_bulk.py --first 10 --count 30 --profile team3-BobbyAWS    # full set t10-t39

Set APPROVED_ID first; the script refuses to run in any other account. Only users tagged
project=team3-test are touched. Removes MFA devices, console passwords and access keys
before deleting each user. Needs: pip install boto3
"""
import argparse, os, sys
import boto3
from botocore.exceptions import ClientError

TAG = {"Key": "project", "Value": "team3-test"}


def code_of(err):
    return err.response["Error"]["Code"]


def cleanup(iam, name):
    try:
        tags = iam.list_user_tags(UserName=name)["Tags"]
    except ClientError as err:
        if code_of(err) == "NoSuchEntity":
            return False
        raise
    if TAG not in tags:
        print(f"skipping {name}: not tagged project=team3-test")
        return False
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
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--first", type=int, required=True)
    p.add_argument("--count", type=int, required=True)
    p.add_argument("--profile")
    a = p.parse_args()
    session = boto3.Session(profile_name=a.profile) if a.profile else boto3.Session()
    if session.client("sts").get_caller_identity()["Account"] != os.environ.get("APPROVED_ID"):
        sys.exit("Refusing to run: this is not the approved account (set APPROVED_ID).")
    iam = session.client("iam")
    removed = 0
    try:
        for n in range(a.first, a.first + a.count):
            removed += cleanup(iam, f"t{n}")
    except ClientError as err:
        info = err.response["Error"]
        sys.exit(f"STOPPED: {info['Code']}: {info.get('Message', '')}")
    print(f"done; removed {removed} user(s)")


if __name__ == "__main__":
    main()
