# Security Runbook

Owner: Security team (Dev Patel, @devp · Yara Haddad, @yarah). Channel: #security.
Report anything suspicious in #security-incidents — false alarms are always welcome; silence is not.

## Reporting a security incident

1. Post in #security-incidents with what you saw and when. Don't investigate on your own first.
2. Security triages within 15 minutes during business hours (PagerDuty `security-oncall` otherwise).
3. Preserve evidence: don't delete emails, close tabs, reboot, or "clean up" before triage.

## Suspected phishing

- Report via the "Report Phishing" button in Gmail (routes to Yara's queue) — even if you clicked.
- **If you clicked a link or entered credentials**: say so immediately. The response is a
  password reset + session revoke, and it takes 10 minutes. There is zero blame attached;
  late reports are the only thing that causes real damage.

## Leaked secret / credential exposure

1. Announce in #security-incidents (Sev2 by default; Sev1 if the secret grants production data access).
2. Rotate first, investigate second — coordinate rotation with #devops (Secrets Manager owners).
3. Purge the secret from git history only *after* rotation; a rotated secret in history is inert.
4. GitHub push protection and the `secret-scan` CI job should have caught it — if they didn't,
   file a gap ticket so the pattern gets added.

## Access control

- Access follows least privilege via Okta groups; every privileged grant has an expiry.
- Production and customer-data access requests need: business reason, duration, manager approval,
  and Security sign-off (SLA: 1 business day).
- Quarterly access reviews: managers certify their team's grants; uncertified access is revoked.

## Laptop / device compromise

Lost, stolen, or behaving strangely (unexpected prompts, new browser extensions, fans at full
speed on idle): #security-incidents first, then IT remote-locks via Jamf (see IT Runbook).
Do not keep using a device you suspect is compromised, even to "back things up".

## Vulnerability management

- Dependabot + weekly Trivy scans feed the vuln board. SLAs: Critical 48 h, High 7 d, Medium 30 d.
- Pentest findings are tracked in the same board with a `pentest` label.
- Disclosure reports from outside researchers go to security@company.com — acknowledge within
  24 h and never dismiss a report without Dev's review.

## Compliance quick answers

SOC 2 Type II report: request via #security (customer-facing copies are watermarked).
Security training: mandatory in the first week and annually — Dev runs the live session.
Vendor reviews: any new SaaS handling customer data needs the vendor questionnaire before purchase.
