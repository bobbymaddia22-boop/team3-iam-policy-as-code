#!/usr/bin/env python3
"""Score the automated and manual MFA audits against the labeled population.

Reads files only. It never calls AWS.

Inputs (CSV):
  --truth      evidence/run-NN/labeled-population.csv
               needs: user_name, expected_status
               optional: console_password, mfa_devices
  --automated  report.csv written by automation/mfa_checker/run_check.py
               needs: user_name, status
               optional: console_access, mfa_device_count
  --manual     the manual audit results file
               needs: user_name and manual_status (or status)
               optional: console_password, mfa_devices

Statuses: COMPLIANT, NON_COMPLIANT, NOT_APPLICABLE. The positive class is NON_COMPLIANT.

For each method it reports the confusion matrix, precision, recall, false-positive
rate and exact status matches. When both methods are given it lists the users where
they disagree. It stops with an error if a user is missing, duplicated, or has an
unknown status, so a broken input file is never scored as a success.

Usage:
  py score_results.py --truth ..\\evidence\\run-02\\labeled-population.csv ^
      --automated ..\\evidence\\run-02\\automated\\report.csv ^
      --manual ..\\evidence\\run-02\\manual-audit.csv ^
      --out-dir ..\\evidence\\run-02

Exit code: 0 = scored, 2 = could not score (bad or missing input).
"""

import argparse
import csv
import json
import sys
from pathlib import Path

VALID_STATUSES = ("COMPLIANT", "NON_COMPLIANT", "NOT_APPLICABLE")
POSITIVE = "NON_COMPLIANT"

CAVEAT = (
    "Scored on a small synthetic population. One misclassified user changes a rate by a "
    "large step, so treat rates as descriptive, not as an estimate of real-world performance."
)


class InputError(Exception):
    """The input could not be scored. The message says why."""


def to_bool(value):
    text = str(value).strip().lower()
    if text in ("true", "yes", "y", "1"):
        return True
    if text in ("false", "no", "n", "0"):
        return False
    return None


def to_int(value):
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def read_rows(path):
    path = Path(path)
    if not path.exists():
        raise InputError(f"File not found: {path.name}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames or []
    if not rows:
        raise InputError(f"{path.name} has no data rows.")
    return rows, [c.strip() for c in columns]


def first_column(columns, candidates):
    for name in candidates:
        if name in columns:
            return name
    return None


def load_statuses(path, label, status_candidates, console_candidates, mfa_candidates):
    """Return {user: {"status", "console", "mfa"}}. Raises InputError on any problem."""
    rows, columns = read_rows(path)
    if "user_name" not in columns:
        raise InputError(f"{label}: column 'user_name' is missing.")
    status_col = first_column(columns, status_candidates)
    if status_col is None:
        raise InputError(f"{label}: needs one of the columns {', '.join(status_candidates)}.")
    console_col = first_column(columns, console_candidates)
    mfa_col = first_column(columns, mfa_candidates)

    result = {}
    for row in rows:
        name = (row.get("user_name") or "").strip()
        if not name:
            raise InputError(f"{label}: a row has an empty user_name.")
        if name in result:
            raise InputError(f"{label}: user '{name}' appears more than once.")
        status = (row.get(status_col) or "").strip().upper()
        if status not in VALID_STATUSES:
            raise InputError(f"{label}: user '{name}' has status '{status}', expected one of {', '.join(VALID_STATUSES)}.")
        result[name] = {
            "status": status,
            "console": to_bool(row[console_col]) if console_col else None,
            "mfa": to_int(row[mfa_col]) if mfa_col else None,
        }
    return result


def load_truth(path):
    return load_statuses(path, "truth", ["expected_status"], ["console_password"], ["mfa_devices"])


def load_automated(path):
    return load_statuses(path, "automated", ["status"], ["console_access"], ["mfa_device_count"])


def load_manual(path):
    return load_statuses(path, "manual", ["manual_status", "status"], ["console_password", "console_access"], ["mfa_devices", "mfa_device_count"])


def ratio(numerator, denominator):
    return None if denominator == 0 else numerator / denominator


def score_method(truth, results, label):
    missing = sorted(set(truth) - set(results))
    extra = sorted(set(results) - set(truth))
    if missing or extra:
        parts = []
        if missing:
            parts.append("missing from results: " + ", ".join(missing))
        if extra:
            parts.append("not in the labeled population: " + ", ".join(extra))
        raise InputError(f"{label}: users do not match the labeled population ({'; '.join(parts)}).")

    tp = fp = fn = tn = exact = 0
    per_user = []
    observation_mismatches = []
    for name in sorted(truth):
        expected = truth[name]["status"]
        actual = results[name]["status"]
        predicted_positive = actual == POSITIVE
        actual_positive = expected == POSITIVE
        if predicted_positive and actual_positive:
            tp += 1
        elif predicted_positive and not actual_positive:
            fp += 1
        elif not predicted_positive and actual_positive:
            fn += 1
        else:
            tn += 1
        if actual == expected:
            exact += 1
        per_user.append({"user_name": name, "expected": expected, "actual": actual, "correct": actual == expected})

        for field, key in (("console_password", "console"), ("mfa_devices", "mfa")):
            t_val, r_val = truth[name][key], results[name][key]
            if t_val is not None and r_val is not None and t_val != r_val:
                observation_mismatches.append(
                    {"user_name": name, "field": field, "labeled": t_val, "recorded": r_val}
                )

    return {
        "label": label,
        "users": len(truth),
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, tp + fn),
        "false_positive_rate": ratio(fp, fp + tn),
        "exact_status_matches": exact,
        "per_user": per_user,
        "observation_mismatches": observation_mismatches,
    }


def find_disagreements(a, b):
    out = []
    for name in sorted(a):
        if name in b and a[name]["status"] != b[name]["status"]:
            out.append({"user_name": name, "automated": a[name]["status"], "manual": b[name]["status"]})
    return out


def fmt(value):
    return "n/a" if value is None else f"{value:.2f}"


def render_markdown(scores, disagreements):
    lines = ["# Scoring results", "", f"Positive class: {POSITIVE}", ""]
    for s in scores:
        c = s["confusion"]
        lines += [
            f"## {s['label']}",
            "",
            f"Users scored: {s['users']}. Exact status matches: {s['exact_status_matches']} of {s['users']}.",
            "",
            "| | Labeled NON_COMPLIANT | Labeled other |",
            "|---|---|---|",
            f"| **Flagged NON_COMPLIANT** | TP = {c['tp']} | FP = {c['fp']} |",
            f"| **Not flagged** | FN = {c['fn']} | TN = {c['tn']} |",
            "",
            f"Precision: {fmt(s['precision'])}  Recall: {fmt(s['recall'])}  False-positive rate: {fmt(s['false_positive_rate'])}",
            "",
            "| User | Expected | Actual | Correct |",
            "|------|----------|--------|---------|",
        ]
        for row in s["per_user"]:
            lines.append(f"| {row['user_name']} | {row['expected']} | {row['actual']} | {'yes' if row['correct'] else 'NO'} |")
        if s["observation_mismatches"]:
            lines += ["", "Recorded facts that differ from the labeled population:", ""]
            for m in s["observation_mismatches"]:
                lines.append(f"- {m['user_name']}: {m['field']} labeled {m['labeled']}, recorded {m['recorded']}")
        lines.append("")
    if disagreements is not None:
        lines += ["## Where the two methods disagree", ""]
        if disagreements:
            lines += ["| User | Automated | Manual |", "|------|-----------|--------|"]
            lines += [f"| {d['user_name']} | {d['automated']} | {d['manual']} |" for d in disagreements]
        else:
            lines.append("They agree on every user.")
        lines.append("")
    lines += ["## Limit", "", CAVEAT, ""]
    return "\n".join(lines)


def run(truth_path, automated_path=None, manual_path=None):
    if not automated_path and not manual_path:
        raise InputError("Give at least one of --automated or --manual.")
    truth = load_truth(truth_path)
    scores = []
    loaded = {}
    if automated_path:
        loaded["automated"] = load_automated(automated_path)
        scores.append(score_method(truth, loaded["automated"], "Automated check"))
    if manual_path:
        loaded["manual"] = load_manual(manual_path)
        scores.append(score_method(truth, loaded["manual"], "Manual audit"))
    disagreements = None
    if "automated" in loaded and "manual" in loaded:
        disagreements = find_disagreements(loaded["automated"], loaded["manual"])
    return scores, disagreements


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score MFA audit results against the labeled population.")
    parser.add_argument("--truth", required=True, help="labeled-population.csv")
    parser.add_argument("--automated", help="report.csv from the automated check")
    parser.add_argument("--manual", help="manual audit results CSV")
    parser.add_argument("--out-dir", help="Write scoring-results.json and scoring-results.md here")
    args = parser.parse_args(argv)

    try:
        scores, disagreements = run(args.truth, args.automated, args.manual)
    except InputError as err:
        print(f"Could not score: {err}", file=sys.stderr)
        return 2

    text = render_markdown(scores, disagreements)
    print(text)

    if args.out_dir:
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "scoring-results.md").write_text(text, encoding="utf-8")
        payload = {"positive_class": POSITIVE, "methods": scores, "disagreements": disagreements, "limit": CAVEAT}
        (out / "scoring-results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {out / 'scoring-results.md'}")
        print(f"Wrote {out / 'scoring-results.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
