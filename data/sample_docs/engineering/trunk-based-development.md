# Trunk-Based Development

Owner: Engineering leadership (James Lee, @jlee). Channel: #engineering.

We practice trunk-based development: everyone integrates into `main` in small steps,
at least daily. Long-lived branches are where merges go to die.

## The rules

1. **`main` is always releasable.** Every commit on `main` passes CI and could deploy.
2. **Branches live < 2 days.** If your branch is older than two days, split the work.
3. **PRs are small.** Target < 400 changed lines. A 1,500-line PR gets slower, worse review
   than three 400-line PRs of the same code — split by refactor/behavior/cleanup.
4. **No release branches** except for the mobile app (store review forces them).
5. **Red `main` stops the line.** Fix or revert within 30 minutes; revert is the default.

## Feature flags, not feature branches

Unfinished work ships dark behind a flag:

- Flags are declared in `flags.yaml` with an owner and an expiry date.
- New flags default OFF in production, ON in staging.
- A flag past its expiry fails the `flag-lint` CI check — flags are scaffolding, not architecture.
- Kill switches for risky paths (new payment flow, migrations) are flags too, and stay.

## Branch-by-abstraction for big changes

Replacing a subsystem? Don't fork the codebase for three weeks. Introduce an abstraction,
put both implementations behind it, migrate callers incrementally on `main`, delete the old one.
The Kafka→Kafka-with-schema-registry migration (ADR-001) is the worked example.

## Merge queue

`main` uses the GitHub merge queue: approved PRs enter the queue, CI runs against the
merged result, and Github lands them serially. Never merge with admin override —
if the queue is stuck, that *is* the incident to fix.

## Commits

Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`) — the changelog
and release notes are generated from them. Squash-merge is the default; the PR title
becomes the commit message, so write PR titles like changelog entries.

## Why we work this way

Integration pain grows with the square of divergence. Small, frequent merges turn
"merge week" into a non-event, make bisecting trivial, keep review honest, and let us
ship any commit at any time. The cost is discipline about flags and slicing work —
ask in #engineering if you're unsure how to slice; slicing is a skill we teach on purpose.
