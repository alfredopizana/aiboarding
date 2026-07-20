# DevOps Runbook

Owner: DevOps team (Lucas Almeida, @lucasa · Nina Petrova, @ninap). Channel: #devops.
Stack: Kubernetes (EKS) · Terraform · GitHub Actions · Grafana/Prometheus · PagerDuty.

## CI/CD

- Pipelines are GitHub Actions; shared workflows live in `company/gha-workflows`.
- A red `main` build is a stop-the-line event: fix or revert within 30 minutes.
  Reverting is not a failure — it is the default remedy.
- Flaky job? Re-run once. If it fails differently, it's not flaky, it's broken.
  Recurring flakes get quarantined via the `flaky` label and a ticket to the owning team (see QA Runbook).

## Deployments

1. Merges to `main` build an image, push to ECR, and deploy to **staging** automatically.
2. Production deploys are promoted from staging via the `deploy-prod` workflow (manual trigger,
   requires the `deployers` GitHub team). Canary at 10% for 15 minutes, then full rollout.
3. Rollback: `deploy-prod` workflow → "rollback" input with the previous image tag,
   or `kubectl rollout undo deployment/<svc> -n prod` in a hurry. Announce either in #devops.
4. Deploy freeze: Fridays after 15:00 local and during incident Sev1/Sev2 — exceptions need Lucas's sign-off.

## Kubernetes basics for service owners

- Access: `aws sso login`, then `aws eks update-kubeconfig --name prod-cluster`.
- Pods crash-looping: `kubectl logs -n prod deploy/<svc> --previous` before restarting anything.
- OOMKilled: raise the memory *limit* only after checking for a leak in Grafana ("Pod memory" board);
  a stair-step graph is a leak, a cliff is load.
- Never `kubectl edit` production resources — everything is GitOps; hand-edits are overwritten
  on the next sync and make drift invisible.

## Terraform

- All infra changes go through PRs in `company/infrastructure`; `terraform plan` runs in CI
  and posts the diff on the PR. Nobody applies locally against production.
- State is in the S3 backend with DynamoDB locking. A stuck lock means someone's apply died:
  confirm in #devops before `terraform force-unlock`.

## Monitoring and alerts

- Dashboards: Grafana folders per team; the "Golden Signals" board is the entry point.
- Every PagerDuty alert must link to a runbook section. An alert without an action is noise —
  delete it or fix it (alert hygiene review happens monthly with @ninap).
- SLOs: availability 99.9% monthly per public service; the error-budget board drives
  the feature-vs-reliability conversation in sprint planning.

## Secrets

Secrets live in AWS Secrets Manager, synced to the cluster via External Secrets Operator.
Rotation is quarterly (calendar owned by Lucas) and immediate on any suspected exposure —
see the Security Runbook for the exposure procedure. Secrets in env files, tickets, or Slack are never acceptable.
