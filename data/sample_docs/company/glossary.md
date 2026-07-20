# Company Glossary

Owner: everyone (PRs welcome — a term you had to ask about belongs here).
Sorted alphabetically. Team names and channels live in the Org Chart doc.

**ADR** — Architecture Decision Record. Immutable write-up of a significant technical decision;
lives in `company/architecture/adr/`. Superseded, never edited.

**Canary** — a production deploy sent to 10% of traffic for 15 minutes before full rollout.
Metrics burn during canary triggers auto-rollback. See DevOps Runbook.

**CE** — Custom Engineering, the team that builds customer-specific integrations. Also the
`found-in-ce` label on product bugs they discover.

**DAG** — Directed Acyclic Graph; in practice, an Airflow pipeline. "The daily DAG is red"
means the morning data pipeline failed. See Data Runbook.

**Design partner** — a customer who gets early access to a feature in exchange for weekly
feedback. Ten design partners is the standard pilot size.

**Error budget** — how much unreliability the SLO allows (99.9% = ~43 min/month). When the
budget is spent, reliability work outranks features. Board: Grafana → "Golden Signals".

**Flag / kill switch** — a feature flag in `flags.yaml`. Kill switches are flags that stay
past launch to turn risky paths off during incidents.

**IC** — Incident Commander (during incidents; not "individual contributor" here — we say
"engineer" for that to avoid exactly this collision). See Incident Management.

**Money paths** — the 12 user journeys covered by the e2e suite (signup, checkout, invite…).
Named in the QA Runbook. "Does it touch a money path?" is a release-risk question.

**Postmortem** — the blameless write-up owed within 5 working days of any Sev1/Sev2.
Template in `company/postmortems/TEMPLATE.md`.

**Quarantine (tests)** — where flaky tests go to be fixed: still running, no longer blocking.
A growing quarantine list is a build-health incident. See QA Runbook.

**Release train** — the staging→production promotion that leaves Tuesdays and Thursdays
16:00 UTC. Miss it, catch the next one — the train doesn't wait.

**RACI** — Responsible / Accountable / Consulted / Informed; the decision-rights matrix.
"Who's the A on this?" is the fastest way to unstick a decision.

**Sev1–Sev4** — incident and bug severity scale, defined in Incident Management and the
QA Runbook. When unsure, pick the higher severity.

**SoW** — Statement of Work; the signed scope for a Custom Engineering engagement.

**SLO** — Service Level Objective, e.g. 99.9% monthly availability. SLOs feed error budgets;
alerts page on burn rate, not on single blips.

**Stop-the-line** — a red `main` build: everyone's top priority until fixed or reverted,
30-minute budget. Borrowed from Toyota; taken literally.

**Values shout-outs** — peer nominations in #kudos read at the monthly all-hands.
