# Practice-account run, 2026-11-07

- Environment: Bobby Maddia's own practice AWS account.
- Population: t1 to t5, built by uild_t1_t5.py (answer key in labeled-population.csv).
- Run identity: an IAM admin user, not the read-only scanner identity.
- Tools: Python 3.13.17, OPA 1.22.2.
- Result: 5 of 5 exact matches; TP=2 (t2, t4), FP=0, FN=0, TN=3. Run time about 1.5 s.
- eport.csv is the checker output with the obby-admin row removed so every user is in the answer key.
- Not blind and not a replacement for the team sandbox run. It shows the checker works on real AWS in a second account.
