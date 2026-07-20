# Custom Engineering Runbook

Owner: Custom Engineering (Grace Okafor, @graceo · Mateo Rossi, @mateor). Channel: #custom-eng.
Mission: deliver customer-specific integrations and professional-services work without forking the product.

## Engagement lifecycle

1. **Intake**: Sales opens a request in the CE board with the signed Statement of Work (SoW).
2. **Scoping**: a solutions engineer writes a one-page technical scope; Grace approves capacity.
3. **Build**: work happens in the `custom-integrations` repo, one directory per customer,
   using only public APIs and webhooks. Product forks are not allowed — if the public API
   can't do it, file a product gap issue instead of patching core.
4. **Handover**: every delivery ends with a runbook page for Support and a recorded demo.

## Customer sandbox environments

- Each active engagement gets a sandbox tenant: `https://<customer>.sandbox.company.com`.
- Request via the `sandbox-provision` GitHub Action (inputs: customer slug, expiry date).
- Sandboxes auto-expire after 60 days; extensions need a note in the SoW ticket.
- Never load real customer production data into a sandbox — synthetic fixtures only.

## Webhook debugging

1. Check delivery attempts in the customer's dashboard → Developers → Webhooks.
2. Replay a failed delivery with `ce-cli webhooks replay <delivery-id>` (idempotent on the customer side
   only if they honor the `Idempotency-Key` header — verify before replaying in bulk).
3. Signature failures are almost always a rotated secret on our side — check the tenant's
   webhook secret age before debugging customer code.

## Escalations from customers

- Integration bug in *our* code: fix in `custom-integrations`, normal PR flow, deploy same day if Sev2+.
- Product bug found during an engagement: file in the product tracker, tag `found-in-ce`,
  and give the customer a workaround — CE does not hotfix product code.
- Angry-customer escalations go to Grace, who owns the communication; engineers stay on the technical thread.

## API rate limits for integrations

Customer integrations share the public API limits (600 req/min per tenant).
For bulk migrations, request a temporary limit raise via #devops at least 48 h in advance —
include tenant, window, and expected request rate. Retry with exponential backoff + jitter;
hammering a 429 extends the tenant's cooldown automatically.
