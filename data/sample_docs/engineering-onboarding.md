# Engineering Onboarding Guide

Welcome to the engineering team! This guide covers your first steps.

## Development environment setup

1. Install Homebrew, then `brew install git node python@3.11 docker`.
2. Clone the main monorepo: `git clone git@github.com:company/monorepo.git`.
3. Run `make bootstrap` — this installs dependencies and pre-commit hooks.
4. Start the local stack with `docker compose up`; the app runs at http://localhost:3000.

If anything fails, ask in #dev-help on Slack or ping your onboarding buddy.

## Code review process

All changes go through pull requests. At least one approval is required.
Keep PRs under 400 lines when possible. CI must be green before merge.
We use conventional commits: feat, fix, chore, docs, refactor.

## On-call and incident response

Engineers join the on-call rotation after their first 90 days.
The incident runbook lives in Confluence under "Platform / Runbooks".
Sev1 incidents page the on-call directly; always open an incident channel.

## Architecture overview

The platform is a set of services behind an API gateway, deployed on Kubernetes.
Core services: auth-service, billing-service, notification-service, and the web app.
Data lives in PostgreSQL with read replicas; events flow through Kafka.
