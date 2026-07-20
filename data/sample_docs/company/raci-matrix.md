# RACI Matrix — Who Decides What

Owner: Operations (Ana Torres, @anat). Reviewed quarterly; propose changes via PR to this doc.

RACI: **R**esponsible does the work · **A**ccountable owns the outcome (exactly one A per row) ·
**C**onsulted gives input before the decision · **I**nformed hears about it after.
If a decision stalls, find the row; if there is no row, the escalation path at the bottom applies.

## Product & engineering

| Decision / activity | Product | Eng team | Platform | DevOps | QA | Security | Data |
|---|---|---|---|---|---|---|---|
| Feature prioritization (roadmap) | **A** | C | C | I | I | I | C |
| Technical design of a feature | C | **A** | C | C | I | C | I |
| Architecture decisions (ADRs) | I | R | **A** | C | I | C | I |
| Production deploy / rollback | I | R | I | **A** | C | I | I |
| Release sign-off | I | R | I | C | **A** | I | I |
| Incident severity & response | I | R | C | R | I | C | I |
| Postmortem action items | I | R | **A** | R | C | C | I |
| Schema changes to tracked events | C | R | I | I | I | I | **A** |

Note: incident command is held by whoever is IC — accountability transfers with the explicit handoff
(see Incident Management), which is why that row has no fixed A.

## Access, tools & spend

| Decision / activity | Requester's manager | IT | Security | Finance |
|---|---|---|---|---|
| Standard app access (Okta catalog) | **A** | R | I | I |
| Privileged / production access | C | R | **A** | I |
| New SaaS vendor (no customer data) | **A** | R | C | C |
| New SaaS vendor (customer data) | C | R | **A** | C |
| Hardware beyond standard issue | **A** | R | I | I |

## People

| Decision / activity | Hiring manager | People Ops | Interview panel | Leadership |
|---|---|---|---|---|
| Opening a role | C | C | — | **A** |
| Hire / no-hire | **A** | C | C | I |
| Compensation bands | I | R | — | **A** |
| Onboarding plan for a new hire | **A** | R | — | I |

## Escalation path

Team lead → functional owner (this matrix) → leadership sync (Tuesdays).
Escalating a stuck decision is a service to the company, not an aggression — say
"I'm escalating so we can move" in the thread and tag both sides. Decisions escalate;
blame doesn't.
