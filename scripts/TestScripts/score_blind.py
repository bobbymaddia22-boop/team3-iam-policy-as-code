"""Score the blind MFA test: checker and manual auditors against the hidden key.
Usage (PowerShell):
  py -3.13 score_blind.py --key bulk_labels_PRIVATE.csv --hash-file build-key-hash.txt `
      --checker checker-run\\report.csv --checker-seconds 4.3647 `
      --audits Audit_Bobby.xlsx Audit_Other.xlsx --out scoring-blind
Needs: pip install openpyxl
"""
import argparse, csv, datetime as dt, hashlib, json, os, re, sys
from openpyxl import load_workbook

POS = "NON_COMPLIANT"
LABELS = ("COMPLIANT", "NON_COMPLIANT", "NOT_APPLICABLE")

def read_text(path):
    b = open(path, "rb").read()
    if b.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\x00" in b:
        return b.decode("utf-16", errors="replace")
    return b.decode("utf-8-sig", errors="replace")

def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest().upper()

def to_seconds(v):
    if isinstance(v, dt.datetime): v = v.time()
    if isinstance(v, dt.time): return v.hour*3600 + v.minute*60 + v.second
    if isinstance(v, (int, float)): return float(v) * 86400
    if isinstance(v, str) and re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", v.strip()):
        p = [int(x) for x in v.strip().split(":")] + [0]
        return p[0]*3600 + p[1]*60 + p[2]
    return None

def audit_status(cp, mfa):
    cp = (cp or "").strip().upper(); mfa = (mfa or "").strip().upper()
    if not cp or not mfa: return "BLANK"
    if "UNSURE" in (cp, mfa): return "UNSURE"
    if cp == "N": return "NOT_APPLICABLE"
    if cp == "Y": return "COMPLIANT" if mfa == "Y" else "NON_COMPLIANT"
    return "BLANK"

def read_audit(path):
    ws = load_workbook(path, data_only=False)["Audit"]
    # Find the two answer columns by their HEADER text, not by position.
    cp_col, mfa_col = 2, 3
    for c in range(2, 6):
        h = str(ws.cell(7, c).value or "").strip().lower()
        if h.startswith("console"): cp_col = c
        elif h.startswith("mfa"): mfa_col = c
    order = "template order" if (cp_col, mfa_col) == (2, 3) else "COLUMNS SWAPPED vs template (read by header names)"
    print(f"{os.path.basename(path)}: console_password in column {cp_col}, mfa in column {mfa_col} ({order})")
    res = {}
    for r in range(8, 8 + 60):
        u = ws.cell(r, 1).value
        if not u or not str(u).startswith("t"): continue
        res[str(u).strip()] = audit_status(ws.cell(r, cp_col).value, ws.cell(r, mfa_col).value)
    s, e = to_seconds(ws["B4"].value), to_seconds(ws["B5"].value)
    minutes = round((e - s) / 60, 1) if s is not None and e is not None and e >= s else None
    return {"name": str(ws["B3"].value or os.path.basename(path)), "status": res, "minutes": minutes, "column_order": order}

def metrics(pred, key):
    users = sorted(key, key=lambda x: int(re.sub(r"\D", "", x) or 0))
    tp = fp = fn = tn = ok = 0; wrong = []
    for u in users:
        p, k = pred.get(u, "MISSING"), key[u]
        if p == k: ok += 1
        else: wrong.append((u, k, p))
        if k == POS and p == POS: tp += 1
        elif k != POS and p == POS: fp += 1
        elif k == POS and p != POS: fn += 1
        else: tn += 1
    n = len(users)
    return {"n": n, "correct": ok, "accuracy": round(ok / n, 4) if n else None,
            "TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "precision": round(tp/(tp+fp), 4) if tp+fp else None,
            "recall": round(tp/(tp+fn), 4) if tp+fn else None, "mismatches": wrong}

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--key", required=True); a.add_argument("--hash-file", required=True)
    a.add_argument("--checker", required=True); a.add_argument("--checker-seconds", type=float)
    a.add_argument("--audits", nargs="*", default=[]); a.add_argument("--out", default="scoring-blind")
    g = a.parse_args()

    saved = re.findall(r"\b[0-9A-Fa-f]{64}\b", read_text(g.hash_file))
    now = sha256(g.key)
    if not saved: sys.exit("Could not find a SHA-256 in the hash file.")
    if now != saved[0].upper():
        sys.exit("STOP: the key file does not match the hash saved at build time. Do not use these results.")
    print("Key hash matches the build-time hash: the key was not changed.")

    key = {}
    with open(g.key, newline="") as fh:
        for row in csv.DictReader(fh): key[row["user_name"].strip()] = row["expected_label"].strip()
    chk = {}
    with open(g.checker, newline="") as fh:
        for row in csv.DictReader(fh): chk[row["user_name"].strip()] = row["status"].strip()

    out = {"key_hash": now, "n_users": len(key), "methods": {}}
    out["methods"]["automated check"] = metrics(chk, key)
    out["methods"]["automated check"]["seconds"] = g.checker_seconds
    audits = [read_audit(p) for p in g.audits]
    for au in audits:
        m = metrics(au["status"], key); m["minutes"] = au["minutes"]; m["column_order"] = au["column_order"]
        out["methods"][f"auditor: {au['name']}"] = m
    disagree = []
    if len(audits) > 1:
        for u in sorted(key, key=lambda x: int(re.sub(r"\D", "", x))):
            vals = {a_["name"]: a_["status"].get(u, "MISSING") for a_ in audits}
            if len(set(vals.values())) > 1: disagree.append((u, vals))
    out["auditor_disagreements"] = disagree

    os.makedirs(g.out, exist_ok=True)
    json.dump(out, open(os.path.join(g.out, "scoring-blind-results.json"), "w"), indent=2)
    L = ["# Blind test scoring", "", f"Key SHA-256 (matches build-time hash): `{now}`", f"Users scored: {len(key)}", "",
         "Positive class: NON_COMPLIANT.", "", "| Method | Correct | Accuracy | TP | FP | FN | TN | Time |", "|---|---|---|---|---|---|---|---|"]
    for name, m in out["methods"].items():
        t = f"{m['seconds']} s" if m.get("seconds") is not None else (f"{m['minutes']} min" if m.get("minutes") is not None else "n/a")
        L.append(f"| {name} | {m['correct']}/{m['n']} | {m['accuracy']} | {m['TP']} | {m['FP']} | {m['FN']} | {m['TN']} | {t} |")
    L += ["", "## Mismatches (user, key, answer)"]
    for name, m in out["methods"].items():
        L.append(f"- {name}: " + ("none" if not m["mismatches"] else "; ".join(f"{u}: key {k}, answered {p}" for u, k, p in m["mismatches"])))
    if disagree:
        L += ["", "## Auditors disagreed on"] + [f"- {u}: {v}" for u, v in disagree]
    open(os.path.join(g.out, "scoring-blind-results.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))

main()
