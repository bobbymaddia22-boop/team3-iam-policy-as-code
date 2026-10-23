# Team 3 Working Agreement

**Last updated:** 2026-10-23
**Agreed by:** [each member confirms in the team channel, with date]

## 1. Roles

| Person | Role | Owns in the repository |
|--------|------|------------------------|
| Bobby Maddia | Testing and Validation Lead | `tests/`, `scripts/`, `evidence/` scoring |
| Carlton | Automated check | `automation/mfa_checker/` |
| Steve | AWS environment and live runs | Sandbox account, run artifacts |
| Venika | Research and Risk Lead | Research findings, `docs/decisions/` |
| Dana DiLeo | Head of Documentation and write-ups | Report, `README.md`, `docs/` wording |

## 2. Channels

| Purpose | Channel | Expected response time |
|---------|---------|------------------------|
| Day-to-day questions | [confirm: group chat name] | [confirm: for example, within 24 hours] |
| Work tracking | GitHub Issues and Milestones | Check before each meeting |
| Meetings | [confirm: day, time, and tool] | Attend, or send notes and updates ahead |
| Urgent blockers | [confirm: how to reach the person] | [confirm] |

## 3. How work moves

- Work is tracked as a GitHub Issue with an owner and a due date.
- Each issue belongs to a Milestone with a real due date (see `docs/schedule.md`).
- Changes go on a branch and merge through a pull request. Nobody commits directly to `main`.
- A pull request needs a review from a teammate other than the author before merging.
- Nothing is committed that contains AWS keys, real account IDs, real user names or emails, unmasked screenshots, or `snapshot.json`.

## 4. Decisions

- Small decisions: the owner of the area decides and notes it in the issue or pull request.
- Decisions that change scope, method, or the evidence we claim: discussed with the whole team and recorded in `docs/decisions/`.
- If the team disagrees, each member states their reasoning in the channel. If the team can't agree within [confirm: for example, two days], the decision goes to [confirm: instructor or agreed tie-break].

## 5. Handling conflict or a missed deadline

1. The person who expects to miss a deadline says so in the channel at least [confirm: for example, 48 hours] before it, with what is done and what is left.
2. The team decides whether to move the task, share it, or reduce scope. The issue and milestone are updated.
3. If a member is unresponsive past [confirm: for example, 72 hours] on a task that blocks others, the team lead raises it with the team, then with the instructor.
4. Disagreements about work are about the work. Keep them in writing in the team channel so there is a record.

## 6. Use of AI tools

Each member discloses AI use in `AI_USE.md` (tool, date, what it did, what was kept or changed, and the checks that were done by a person).
