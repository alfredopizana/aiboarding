# Platform Architecture Overview

Owner: Platform team (María Gómez, @maria). Channel: #platform.
Diagrams are Mermaid — they render on GitHub, in VS Code, and at https://mermaid.live.

## System context

The platform is a set of services behind an API gateway, deployed on Kubernetes (EKS).
PostgreSQL is the system of record, Kafka carries domain events, Redis handles caching
and rate limiting. The marketing site and web app are separate Next.js deployments on Vercel.

```mermaid
flowchart LR
    subgraph Clients
        WEB[Web app - Next.js]
        MOB[Mobile app]
        API_CUST[Customer integrations]
    end
    subgraph Edge
        CDN[CDN / WAF]
        GW[API Gateway]
    end
    subgraph Services [Kubernetes - prod cluster]
        AUTH[auth-service]
        BILL[billing-service]
        NOTIF[notification-service]
        CORE[core-api]
    end
    subgraph DataStores [Data]
        PG[(PostgreSQL + read replicas)]
        KAFKA[[Kafka]]
        REDIS[(Redis)]
        SNOW[(Snowflake DWH)]
    end
    WEB --> CDN --> GW
    MOB --> CDN
    API_CUST --> GW
    GW --> AUTH & CORE
    CORE --> BILL & PG & REDIS
    CORE -- events --> KAFKA
    KAFKA --> NOTIF
    KAFKA -- CDC / ELT --> SNOW
```

## Service responsibilities

- **auth-service** — sessions, tokens, SSO (Okta SAML/OIDC), API keys. Owns the `users` schema.
- **core-api** — the domain: workspaces, projects, documents. Everything else hangs off it.
- **billing-service** — subscriptions and invoicing; wraps Stripe, emits `invoice.*` events.
- **notification-service** — consumes Kafka events, fans out to email/Slack/webhooks.

Rule of thumb: services communicate synchronously through the gateway *or* asynchronously
via Kafka events — never by reaching into another service's database.

## Request lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant G as API Gateway
    participant A as auth-service
    participant S as core-api
    participant K as Kafka
    C->>G: POST /v1/projects (JWT)
    G->>A: validate token (cached 60s)
    A-->>G: claims
    G->>S: forward + trace headers
    S->>S: authorize, write to PostgreSQL
    S->>K: publish project.created
    S-->>C: 201 + project
    Note over K: notification-service and DWH consume asynchronously
```

## Deployment pipeline

```mermaid
flowchart LR
    PR[Pull request] --> CI{CI: tests + lint + scan}
    CI -->|green + review| M[Merge to main]
    M --> B[Build image → ECR]
    B --> STG[Auto-deploy staging]
    STG --> E2E{e2e suite}
    E2E -->|pass| CAN[Canary 10% / 15 min]
    CAN -->|metrics healthy| PROD[Full production rollout]
    CAN -->|error budget burn| RB[Auto-rollback]
```

Details: DevOps Runbook (promotion, rollback, freeze windows).

## Cross-cutting decisions (ADRs)

Architecture Decision Records live in `company/architecture/adr/` — one file per decision,
never edited after acceptance, superseded by a new ADR instead. Start with
ADR-001 (event schema versioning), ADR-007 (multi-tenancy via schema-per-tenant rejected),
and ADR-012 (why the gateway owns authn but services own authz).

## Non-functional targets

Availability 99.9%/month per public service · p95 API latency < 300 ms ·
RPO 5 min / RTO 1 h (cross-region PostgreSQL replicas) · all data encrypted in transit and at rest.
