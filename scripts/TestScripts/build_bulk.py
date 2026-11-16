import boto3, csv, os, random, secrets, sys, time, pyotp
from botocore.exceptions import ClientError

COUNT = 30   # use 3 for the pilot
FIRST = 10   # the first new bulk user is t10 (t1-t9 are already used)
LABELS_FILE = "bulk_labels_PRIVATE.csv"
TAG = [{"Key": "project", "Value": "team3-test"}]

iam = boto3.client("iam")
sts = boto3.client("sts")

# Safety: refuse to build anywhere except the approved sandbox (ID is never printed).
if sts.get_caller_identity()["Account"] != os.environ.get("APPROVED_ID"):
    sys.exit("Refusing to build: not the approved sandbox account (set APPROVED_ID).")

per = COUNT // 3
labels = (["COMPLIANT"] * per + ["NON_COMPLIANT"] * per
          + ["NOT_APPLICABLE"] * (COUNT - 2 * per))
random.shuffle(labels)

def new_password():
    return secrets.token_urlsafe(24) + "aA1!"

def retry(call, **kwargs):
    """IAM can lag right after create_user; retry NoSuchEntity a few times."""
    for attempt in range(6):
        try:
            return call(**kwargs)
        except ClientError as err:
            if err.response["Error"]["Code"] != "NoSuchEntity" or attempt == 5:
                raise
            time.sleep(2)

# "x" mode refuses to overwrite labels left over from an earlier partial run.
with open(LABELS_FILE, "x", newline="") as fh:
    out = csv.writer(fh)
    out.writerow(["user_name", "expected_label"])
    for i, label in enumerate(labels, start=1):
        name = f"t{FIRST + i - 1}"
        out.writerow([name, label])   # write the intended state BEFORE building
        fh.flush()
        try:
            iam.create_user(UserName=name, Tags=TAG)
            if label in ("COMPLIANT", "NON_COMPLIANT"):
                retry(iam.create_login_profile, UserName=name, Password=new_password())
            if label == "COMPLIANT":
                dev = iam.create_virtual_mfa_device(
                    VirtualMFADeviceName=f"{name}-mfa", Tags=TAG)["VirtualMFADevice"]
                totp = pyotp.TOTP(dev["Base32StringSeed"].decode())
                now = time.time()
                retry(iam.enable_mfa_device, UserName=name,
                      SerialNumber=dev["SerialNumber"],
                      AuthenticationCode1=totp.at(now),
                      AuthenticationCode2=totp.at(now + 30))
            if label == "NOT_APPLICABLE" and i % 2 == 0:
                iam.create_access_key(UserName=name)   # secret is discarded, never saved
        except ClientError as err:
            sys.exit(f"STOPPED at {name}: {err.response['Error']['Code']}. "
                     f"{name} may be half built; check it and clean it up. "
                     f"Labels for t{FIRST}-{name} are saved in {LABELS_FILE}.")
print("built", COUNT, "users; labels written to", LABELS_FILE)
