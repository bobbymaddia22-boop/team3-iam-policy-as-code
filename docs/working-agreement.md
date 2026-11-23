# Team 3 Working Agreement

**Last updated:** 2026-11-22
**Agreed by:** Team 3 members, confirmed in the team channel

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
| Day-to-day questions | Team group chat | Within 24 hours |
| Work tracking | GitHub Issues and Milestones | Check before each meeting |
| Meetings | Scheduled in the group chat | Attend, or send notes and updates ahead |
| Urgent blockers | Message the person directly and post in the group chat | Within 12 hours |

## 3. How work moves

- Work is tracked as a GitHub Issue with an owner and a due date.
- Each issue belongs to a Milestone with a real due date (see `docs/schedule.md`).
- Changes go on a branch and merge through a pull request. Nobody commits directly to `main`.
- A pull request needs a review from a teammate other than the author before merging.
- Nothing is committed that contains AWS keys, real account IDs, real user names or emails, unmasked screenshots, or `snapshot.json`.

## 4. Decisions

- Small decisions: the owner of the area decides and notes it in the issue or pull request.
- Decisions that change scope, method, or the evidence we claim: discussed with the whole team and recorded in `docs/decisions/`.
- If the team disagrees, each member states their reasoning in the channel. If the team can't agree within two days, the decision goes to the instructor.

## 5. Handling conflict or a missed deadline

1. The person who expects to miss a deadline says so in the channel at least 48 hours before it, with what is done and what is left.
2. The team decides whether to move the task, share it, or reduce scope. The issue and milestone are updated.
3. If a member is unresponsive for more than 72 hours on a task that blocks others, the team lead raises it with the team, then with the instructor.
4. Disagreements about work are about the work. Keep them in writing in the team channel so there is a record.

## 6. Use of AI tools

Each member discloses AI use in the AI Development Log and Prompt Appendix submitted with the project: tool and model, date, purpose, the prompt, whether the output was used, what was changed, and the checks a person did.
