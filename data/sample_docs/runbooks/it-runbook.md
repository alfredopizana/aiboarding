# IT Runbook

Owner: IT team (Raj Singh, @rajs · Claire Dubois, @claired). Channel: #it-helpdesk.
Ticket queue: https://helpdesk.company.com. SLA: P1 30 min, P2 4 h, P3 next business day.

## New hire provisioning (day 0)

1. HR ticket auto-creates the provisioning task 5 business days before start date.
2. Create the Google Workspace account (`first.last@company.com`) from the `new-hire` template.
3. Assign the Okta profile and the baseline app grants: Slack, GitHub, Notion, Zoom.
4. Enroll the laptop in Jamf MDM before shipping; verify FileVault encryption is on.
5. Send the welcome email with the first-login checklist and #it-helpdesk link.

Role-based extras: engineers get AWS SSO + PagerDuty; data team gets Snowflake + Airflow;
custom engineering gets the customer sandbox VPN profile.

## Laptop issues

- **Won't boot / hardware fault**: open a P2 ticket, IT ships a loaner within 24 h (48 h outside HQ regions).
- **Slow machine**: check Jamf inventory for pending OS updates; 8 GB models are eligible for refresh.
- **Lost or stolen**: this is a security incident — page Security via #security-incidents *first*,
  then remote-lock via Jamf and file the P1 ticket.

## Account and access requests

- All access goes through Okta self-service; managers approve within the request flow.
- Privileged access (production, billing, customer data) additionally requires Security approval —
  see the access-control section of the Security Runbook.
- Never share accounts. Service accounts are requested via #it-helpdesk with an owner and expiry.

## VPN

1. Install the WireGuard profile from Okta → "VPN Access".
2. If the tunnel connects but nothing resolves, toggle the DNS profile in Jamf Self Service.
3. Contractor VPN certs expire every 90 days; renewals are self-service in Okta.

## Password / MFA resets

Identity checks are mandatory: verify via video call + employee ID before any reset.
Resets happen in Okta admin; never send passwords over Slack or email.

## Offboarding

Within 1 hour of the HR trigger: suspend Okta (cascades SSO), revoke Google Workspace,
remote-wipe the laptop if remote, reassign licenses, transfer Drive ownership to the manager.
