# Scoring results

Positive class: NON_COMPLIANT

## Automated check

Users scored: 8. Exact status matches: 8 of 8.

| | Labeled NON_COMPLIANT | Labeled other |
|---|---|---|
| **Flagged NON_COMPLIANT** | TP = 4 | FP = 0 |
| **Not flagged** | FN = 0 | TN = 4 |

Precision: 1.00  Recall: 1.00  False-positive rate: 0.00

| User | Expected | Actual | Correct |
|------|----------|--------|---------|
| t1 | COMPLIANT | COMPLIANT | yes |
| t2 | NON_COMPLIANT | NON_COMPLIANT | yes |
| t3 | NOT_APPLICABLE | NOT_APPLICABLE | yes |
| t4 | NON_COMPLIANT | NON_COMPLIANT | yes |
| t5 | COMPLIANT | COMPLIANT | yes |
| t6 | NOT_APPLICABLE | NOT_APPLICABLE | yes |
| t7 | NON_COMPLIANT | NON_COMPLIANT | yes |
| t8.test+mfa,Case=A@team3 | NON_COMPLIANT | NON_COMPLIANT | yes |

## Limit

Scored on a small synthetic population. One misclassified user changes a rate by a large step, so treat rates as descriptive, not as an estimate of real-world performance.
