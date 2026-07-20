# Data Team Runbook

Owner: Data team (Priya Nair, @priyan · Tomáš Novák, @tomasn). Channel: #data-eng.
Stack: Snowflake (warehouse) · Airflow (orchestration) · dbt (transformations) · Looker (BI).

## Daily pipeline health check

1. Open the Airflow UI (https://airflow.internal.company.com) and check the `daily_core` DAG.
2. All tasks green by 07:00 UTC is the SLO. Amber after 07:30, incident after 09:00.
3. dbt test results land in #data-eng via the `dbt-runner` bot; failures block downstream dashboards.

## Failed Airflow DAG

1. Check the task logs in the Airflow UI — most failures are upstream API timeouts.
2. Retry the failed task once (`Clear` → run). Two consecutive failures → escalate.
3. If the failure is in an ingestion task, check the source system status page before blaming the DAG.
4. Backfills: `airflow dags backfill daily_core -s <start> -e <end>` — always announce in #data-eng first,
   backfills consume the same warehouse credits as production runs.

## Snowflake issues

- **Query queue building up**: check for runaway queries in the `COMPUTE_WH` monitor; kill queries
  older than 30 min after posting a warning in #data-eng.
- **Credit burn alert**: the resource monitor suspends the warehouse at 110% of the daily budget.
  Only Priya or the on-call data engineer may resume it.
- **Access requests**: read access to curated schemas (`ANALYTICS.*`) is self-service via Okta.
  Raw schemas (`RAW.*`) contain unmasked PII and require Security sign-off.

## Broken dashboard

1. Confirm whether the underlying dbt model ran today (`dbt ls --select <model>+` lineage helps).
2. If data is stale, it's a pipeline issue → treat as failed DAG above.
3. If numbers look wrong, check the dbt test history before editing the dashboard —
   most "wrong numbers" are a definition change, not a bug. Definitions live in the metrics
   layer (`dbt/models/marts/`), and changes require a PR reviewed by analytics.

## Event tracking changes

New product events follow the tracking plan in Notion ("Data / Tracking Plan").
Schema changes to events require a PR against `schemas/events/` and a heads-up to @tomasn —
undeclared schema changes are the #1 cause of silently broken funnels.

## Data incident (wrong data shipped to customers)

Treat as Sev2 minimum: open an incident channel, freeze the affected pipeline,
snapshot the bad state (`CREATE TABLE ... CLONE`), fix forward, then run reconciliation.
Never delete the evidence tables before the postmortem.
