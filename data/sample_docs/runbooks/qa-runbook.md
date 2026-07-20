# QA Runbook

Owner: QA team (Ken Watanabe, @kenw · Elena Duarte, @elenad). Channel: #qa.
Philosophy: QA owns the quality *system*; every engineer owns the quality of their change.

## Test pyramid and where tests live

- **Unit**: next to the code, run on every PR (`make test`). Target < 5 min total.
- **API/integration**: `tests/integration/` per service, run on every PR against ephemeral deps.
- **End-to-end**: Playwright suite in `company/e2e`, runs on merge to `main` and hourly against staging.
  E2E covers the 12 "money paths" (signup, login, checkout, invite, export…) — resist adding more;
  breadth belongs in lower layers.

## Release sign-off

1. The release train leaves staging Tuesdays and Thursdays at 16:00 UTC.
2. Sign-off checklist (owned by Ken): green e2e run, no open Sev1/Sev2 bugs on the release board,
   feature flags for unfinished work verified OFF in prod config.
3. Sign-off is recorded in #qa with the run link — "LGTM in a thread" doesn't count.

## Bug triage

- New bugs land in the triage column; QA triages daily at 10:00 UTC (15 min, #qa huddle).
- Severity: **Sev1** data loss/security/site down · **Sev2** core flow broken, no workaround ·
  **Sev3** broken with workaround · **Sev4** cosmetic.
- Every bug needs: steps to reproduce, expected vs actual, environment, and evidence
  (screenshot/HAR/video). Bugs without repro steps go back to the reporter, kindly.

## Flaky tests

A test that fails then passes on retry is quarantined, not deleted:
1. Label `flaky`, move to the quarantine suite (still runs, doesn't block).
2. Owning team gets a ticket with the failure fingerprint; budget: fix within 2 sprints.
3. Elena reviews the quarantine list weekly — a growing list is a build-health incident.
Root causes in order of frequency: unawaited async, shared test data, time/timezone assumptions.

## Writing a good e2e test

- Use role/label selectors (`getByRole`), never CSS classes or nth-child.
- Each test creates its own data via the API fixtures helper — no shared accounts.
- Assert on user-visible outcomes, not network calls.
- If it needs a `waitForTimeout`, it's wrong — wait on a condition instead.

## Test environments

- **staging**: production-like, seeded nightly, safe to break, reset via `make reset-staging`.
- **preview-<pr>**: per-PR ephemeral env for services that support it (see DevOps Runbook).
- Test accounts: `qa+<anything>@company.com` — mail is captured in Mailhog (https://mail.staging.company.com).
