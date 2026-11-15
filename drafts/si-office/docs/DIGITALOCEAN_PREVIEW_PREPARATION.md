# CFP+ • DigitalOcean priority / Render comparison • HOLD

13/10/2026. HOLD ACTIVATION • CONDITIONAL APPROVAL • PRODUCTION NO-GO.

Current CFP+ direction prioritizes DigitalOcean12.20USD before tax/fees and keeps
Render12.25USD with external Spaces storage as comparison. No purchase decision.
This document supersedes the provider preference in PREVIEW_SINGLE_CANDIDATE.md
for this preparation only; it preserves that historical candidate/evidence.
Preferred Preview remains f3be4842d973e2e882102ed16376a57954d87d63; comparison
2814b357d8b31385aff530ca37eb8606674b608e is immutable. Technical/training draft
base42e8baeed1b6fd2e6114b7b54c69c94747aee51f is not auto-approved for hosting.

## Verified list-price basis, not account checkout

| Item | Proposed DigitalOcean configuration | USD/month before tax/fees |
|---|---|---:|
| Host | Basic Regular bundled s-1vcpu-1gb,1vCPU/1GiB/25GiB SSD |6.00|
| Storage | One Standard Spaces subscription; private buckets;250GiB/1TiB included |5.00|
| Image backup | Percentage-based weekly20% of6USD |1.20|
| Total | One Preview host; no autoscale/additional disks/LB/managed DB/domain |12.20|

Official sources read13/10/2026: [host](https://www.digitalocean.com/pricing/droplets),
[Spaces](https://www.digitalocean.com/pricing/spaces-object-storage),
[backup](https://docs.digitalocean.com/products/backups/details/pricing/).
SGP1 is proposed, plan/availability/account quota not confirmed. Node24, private
SQLite directory0700/DB0600, one writer, Caddy/ACME HTTPS, exact Host/Origin/Secure
cookie and synthetic reviewer grants are required, not configured in cloud.

The earlier source CFP_PREVIEW_APPROVAL_VI.md exists in this session's workspace;
its12.20 breakdown matches the three primary sources above. The previous
candidate reported it absent in its workspace: a scope-dependent missing-source
report, not proof the plan did not exist. This durable repo document makes the
price/config basis accessible without sharing credentials or creating a host.

Render comparison12.25 =7USD paid0.5CPU/512MB +0.25USD1GB persistent disk +5USD
external Spaces. Do not add DO1.20 image backup to Render. The old7.25 estimate
excluded confirmed external backup cost. Source:
[Render pricing](https://render.com/pricing), [disk](https://render.com/docs/disks).
Neither total includes tax/payment/FX/shared usage/overage. Render uses GB while
DO allowances are GiB/TiB; compare actual billing units. No two Preview resources.

## New kernel-meter and HTTPS-close evidence

kernel-egress-guard.py samples tx_bytes of every NIC visible in the current guest
network namespace, including lo; this includes traffic bypassing the application
proxy and both IP families on those NICs. A changed NIC set/counter reset, expired
lease, stale/missing quote or forecast>1500c closes the callback and persists
CLOSED. Default approval is false; no cloud API, public bind, firewall/DNS action
or runnable production CLI is provided. No re-arm existing state.

Six NEW tests in tests/kernel-egress-https.py ran on actual kernel counters and
temporary TLS1.2+ localhost sockets: TLS traffic observed; direct IPv4/IPv6 UDP
outside proxy triggered closure; external local probe confirmed HTTPS listener
unreachable; CLOSED cannot re-arm; meter loss, forecast>15, expiry closed HTTPS;
no authority did not arm. The6 tests passed, synthetic quote1342c, no public URL.
The first run exposed incorrect classification of an expected missing-meter
trigger as a closure error; that telemetry was corrected and only the changed
new scope rerun. Prior ledger8/8, proxy8/8, training/Core/Routing PASS not rerun.

## Remaining blockers — do not call local proof global provider PASS

Guest counters do not cover sidecars, cloud edge, another namespace/host, direct
Spaces downloads or provider-delayed billing. Loopback can be counted twice and
NIC-summed traffic is conservative, not invoice-equivalent. Polling allows
overshoot during the interval; no zero-overshoot hard cap. No actual DO public
NIC/firewall/SSH deployment or end-to-end observer exists yet.

The close callback stopped a real fixture HTTPS listener, not Caddy/Render/DO
infrastructure or a production process. On a real host, the owner must bind the
callback to outer HTTPS closure, close active streams, preserve an admin path,
confirm remotely, and use independently fail-closed firewall/boot arming if the
watchdog crashes or disk cannot persist CLOSED. No unattended restart/resume.

Account quota/usage/tax/fees/FX/checkout and pending charges are MISSING EVIDENCE.
The quote boolean in tests is not verified Human Governance approval. Keeping
public admission CLOSED does not stop Droplet/Spaces/backup or accrued billing.
[Powered-off billing](https://docs.digitalocean.com/products/droplets/details/pricing/)
and [Spend Alerts](https://docs.digitalocean.com/platform/billing/spend-alerts/)
must not be treated as a money cap. Teardown requires separate authority and
backup verification; none is granted in this preparation.

[Bandwidth billing](https://docs.digitalocean.com/platform/billing/bandwidth/)
confirms public-NIC transfer and cumulative team allowance accrued over runtime,
not all1000GiB at creation. Example1000GiB/28days≈1.488GiB/hour; about0.372GiB after
15minutes, before other team usage. Proposed5GiB lease must be lowered against
actual remaining allowance, including backup transfer and pending usage. Do not
assume the5GiB guard guarantees no overage at first boot. Spaces download quota
and key/ACL controls must be verified separately; no public/direct exports.

Human Governance owns payment and backup; Codex technical preparation under CFP+
oversight. Named contacts/backup custody/SSH/operator lease remain missing.
Short checkout instructions: CHECKOUT_SHORT_VI.md. Host restore/process-switch
rehearsal awaits authorized host/environment; never overwrite existing DB/audit.
MCP/CMP retain independent exceptions. No paid resources/payment entry/DNS/merge/
production/real adapter, ID/Parent/DID/Canonical or historical-audit changes.
