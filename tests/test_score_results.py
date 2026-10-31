"""Unit tests for scripts/score_results.py. Standard library only, no AWS needed.

Run from the repo root:  py -m unittest discover -s tests -v
"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import score_results as sr  # noqa: E402

TRUTH = """user_name,console_password,mfa_devices,configuration,expected_status
t1,true,1,x,COMPLIANT
t2,true,0,x,NON_COMPLIANT
t3,false,0,x,NOT_APPLICABLE
t4,true,0,x,NON_COMPLIANT
t5,true,2,x,COMPLIANT
"""

AUTO_PERFECT = """user_name,console_access,mfa_device_count,status
t1,True,1,COMPLIANT
t2,True,0,NON_COMPLIANT
t3,False,0,NOT_APPLICABLE
t4,True,0,NON_COMPLIANT
t5,True,2,COMPLIANT
"""

MANUAL_PERFECT = """user_name,console_password,mfa_devices,manual_status
t1,yes,1,COMPLIANT
t2,yes,0,NON_COMPLIANT
t3,no,0,NOT_APPLICABLE
t4,yes,0,NON_COMPLIANT
t5,yes,2,COMPLIANT
"""


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return str(path)


class ScoringTests(Base):
    def test_perfect_automated(self):
        scores, dis = sr.run(self.write("t.csv", TRUTH), self.write("a.csv", AUTO_PERFECT))
        s = scores[0]
        self.assertEqual(s["confusion"], {"tp": 2, "fp": 0, "fn": 0, "tn": 3})
        self.assertEqual(s["precision"], 1.0)
        self.assertEqual(s["recall"], 1.0)
        self.assertEqual(s["false_positive_rate"], 0.0)
        self.assertEqual(s["exact_status_matches"], 5)
        self.assertIsNone(dis)

    def test_missed_noncompliant_user_is_false_negative(self):
        bad = AUTO_PERFECT.replace("t4,True,0,NON_COMPLIANT", "t4,True,0,COMPLIANT")
        s = sr.run(self.write("t.csv", TRUTH), self.write("a.csv", bad))[0][0]
        self.assertEqual(s["confusion"], {"tp": 1, "fp": 0, "fn": 1, "tn": 3})
        self.assertEqual(s["recall"], 0.5)
        self.assertEqual(s["precision"], 1.0)

    def test_extra_flag_is_false_positive(self):
        bad = AUTO_PERFECT.replace("t3,False,0,NOT_APPLICABLE", "t3,False,0,NON_COMPLIANT")
        s = sr.run(self.write("t.csv", TRUTH), self.write("a.csv", bad))[0][0]
        self.assertEqual(s["confusion"], {"tp": 2, "fp": 1, "fn": 0, "tn": 2})
        self.assertAlmostEqual(s["precision"], 2 / 3)
        self.assertAlmostEqual(s["false_positive_rate"], 1 / 3)

    def test_wrong_status_between_negative_classes_is_not_exact_match(self):
        # COMPLIANT vs NOT_APPLICABLE: neither is the positive class, but it is still wrong.
        bad = AUTO_PERFECT.replace("t3,False,0,NOT_APPLICABLE", "t3,False,0,COMPLIANT")
        s = sr.run(self.write("t.csv", TRUTH), self.write("a.csv", bad))[0][0]
        self.assertEqual(s["confusion"]["fn"], 0)
        self.assertEqual(s["confusion"]["fp"], 0)
        self.assertEqual(s["exact_status_matches"], 4)

    def test_rates_are_none_when_denominator_is_zero(self):
        truth = "user_name,expected_status\nt1,COMPLIANT\nt2,COMPLIANT\n"
        auto = "user_name,status\nt1,COMPLIANT\nt2,COMPLIANT\n"
        s = sr.run(self.write("t.csv", truth), self.write("a.csv", auto))[0][0]
        self.assertIsNone(s["precision"])
        self.assertIsNone(s["recall"])
        self.assertEqual(s["false_positive_rate"], 0.0)

    def test_manual_accepts_status_column_name(self):
        manual = "user_name,status\n" + "\n".join(
            f"{r['user_name']},{r['expected']}" for r in sr.score_method(
                sr.load_truth(self.write("t.csv", TRUTH)), sr.load_truth(self.write("t2.csv", TRUTH)), "x")["per_user"]
        ) + "\n"
        scores, _ = sr.run(self.write("t3.csv", TRUTH), manual_path=self.write("m.csv", manual))
        self.assertEqual(scores[0]["exact_status_matches"], 5)

    def test_both_methods_report_disagreements(self):
        manual = MANUAL_PERFECT.replace("t2,yes,0,NON_COMPLIANT", "t2,yes,0,COMPLIANT")
        scores, dis = sr.run(self.write("t.csv", TRUTH), self.write("a.csv", AUTO_PERFECT), self.write("m.csv", manual))
        self.assertEqual(len(scores), 2)
        self.assertEqual(dis, [{"user_name": "t2", "automated": "NON_COMPLIANT", "manual": "COMPLIANT"}])

    def test_observation_mismatch_is_reported(self):
        # The method recorded one MFA device for t2, but the labeled population says zero.
        bad = AUTO_PERFECT.replace("t2,True,0,NON_COMPLIANT", "t2,True,1,NON_COMPLIANT")
        s = sr.run(self.write("t.csv", TRUTH), self.write("a.csv", bad))[0][0]
        self.assertEqual(
            s["observation_mismatches"],
            [{"user_name": "t2", "field": "mfa_devices", "labeled": 0, "recorded": 1}],
        )

    def test_bool_parsing(self):
        for value in ("True", "true", "YES", "1"):
            self.assertIs(sr.to_bool(value), True)
        for value in ("False", "no", "0"):
            self.assertIs(sr.to_bool(value), False)
        self.assertIsNone(sr.to_bool("maybe"))


class InputErrorTests(Base):
    def assert_input_error(self, truth=TRUTH, auto=AUTO_PERFECT, fragment=""):
        with self.assertRaises(sr.InputError) as ctx:
            sr.run(self.write("t.csv", truth), self.write("a.csv", auto))
        self.assertIn(fragment, str(ctx.exception))

    def test_missing_user_is_an_error_not_a_silent_skip(self):
        short = "\n".join(AUTO_PERFECT.splitlines()[:-1]) + "\n"
        self.assert_input_error(auto=short, fragment="missing from results: t5")

    def test_extra_user_is_an_error(self):
        self.assert_input_error(auto=AUTO_PERFECT + "t9,True,1,COMPLIANT\n", fragment="not in the labeled population: t9")

    def test_duplicate_user_is_an_error(self):
        self.assert_input_error(auto=AUTO_PERFECT + "t1,True,1,COMPLIANT\n", fragment="more than once")

    def test_unknown_status_is_an_error(self):
        self.assert_input_error(auto=AUTO_PERFECT.replace("COMPLIANT\nt2", "PASS\nt2", 1), fragment="PASS")

    def test_header_only_file_is_an_error(self):
        self.assert_input_error(auto="user_name,console_access,mfa_device_count,status\n", fragment="no data rows")

    def test_empty_file_is_an_error(self):
        self.assert_input_error(auto="", fragment="no data rows")

    def test_missing_status_column_is_an_error(self):
        self.assert_input_error(auto="user_name,console_access\nt1,True\n", fragment="needs one of the columns")

    def test_missing_file_is_an_error(self):
        with self.assertRaises(sr.InputError):
            sr.run(self.write("t.csv", TRUTH), str(self.dir / "nope.csv"))

    def test_nothing_to_score_is_an_error(self):
        with self.assertRaises(sr.InputError):
            sr.run(self.write("t.csv", TRUTH))


class CommandLineTests(Base):
    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sr.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_exit_zero_and_files_written(self):
        out_dir = self.dir / "out"
        code, stdout, _ = self.run_main([
            "--truth", self.write("t.csv", TRUTH),
            "--automated", self.write("a.csv", AUTO_PERFECT),
            "--manual", self.write("m.csv", MANUAL_PERFECT),
            "--out-dir", str(out_dir),
        ])
        self.assertEqual(code, 0)
        self.assertIn("They agree on every user.", stdout)
        self.assertTrue((out_dir / "scoring-results.md").exists())
        self.assertTrue((out_dir / "scoring-results.json").exists())

    def test_exit_two_on_bad_input(self):
        code, _, stderr = self.run_main([
            "--truth", self.write("t.csv", TRUTH),
            "--automated", self.write("a.csv", ""),
        ])
        self.assertEqual(code, 2)
        self.assertIn("Could not score", stderr)

    def test_wrong_scoring_still_exits_zero(self):
        # Low accuracy is a result, not a failure to run.
        bad = AUTO_PERFECT.replace("t4,True,0,NON_COMPLIANT", "t4,True,0,COMPLIANT")
        code, stdout, _ = self.run_main(["--truth", self.write("t.csv", TRUTH), "--automated", self.write("a.csv", bad)])
        self.assertEqual(code, 0)
        self.assertIn("FN = 1", stdout)


if __name__ == "__main__":
    unittest.main()
