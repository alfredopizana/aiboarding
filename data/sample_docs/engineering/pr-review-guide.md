# How to Review a Pull Request

Owner: Engineering (Leo Martins, @leom, runs the review workshop). Channel: #engineering.
Reviews exist to ship better code sooner — not to prove the reviewer is clever.

## Service levels

- First response within **4 working hours**; small PRs (< 100 lines) same half-day.
- One approval required everywhere; two for auth, billing, and infrastructure paths (CODEOWNERS enforces this).
- If you can't review in time, say so and name someone — silence blocks a teammate.

## How to review (in this order)

1. **Read the description first.** What problem is this solving? If you can't tell, that's
   your first comment — don't reverse-engineer intent from the diff.
2. **Does the approach make sense?** Architecture concerns come before line comments.
   A perfect implementation of the wrong design is still wrong.
3. **Correctness**: edge cases, error paths, concurrency, migrations that lock tables.
4. **Tests**: does a test fail if the behavior regresses? Coverage of the *change*, not the number.
5. **Security**: input validation, authz on new endpoints, secrets, PII in logs.
6. Style nits last, and only ones the linter can't catch — prefix them with `nit:`.

## Comment etiquette

- Comment on the code, never the author: "this function re-reads the file per item" not "you're re-reading".
- Ask real questions, not rhetorical ones. "What happens if the list is empty?" invites an answer;
  "Did you even test this?" invites a resignation.
- Distinguish blocking from non-blocking explicitly: `blocking:` / `nit:` / `question:` / `praise:`.
- Praise in review is data too — call out things worth copying.
- Three comment-rounds without convergence → 15-minute call, then record the outcome on the PR.

## For authors

- Keep PRs < 400 lines; describe *why*, link the issue, include screenshots for UI and
  the rollout/rollback note for risky changes.
- Review your own diff before requesting review — you'll catch a third of the comments yourself.
- Don't force-push after review starts; push fixup commits so reviewers see what changed.
- Disagree openly when you disagree. "Done" on a comment you think is wrong helps nobody.

## Approving

Approve means "I understand this change and I'm happy for it to ship under both our names."
LGTM-without-reading shows up in incident timelines with your handle on it.
Rubber-stamp streaks are visible in the review analytics Ken's team publishes monthly.

## What reviews are not for

Relitigating settled conventions (open an RFC instead), demanding unrelated refactors
("while you're here…" is how 400-line PRs become 1,500), or perfectionism on code
behind an expiring feature flag. Ratchet quality on the paths that stay.
