# CFP+ App and multi-agent feasibility — 2026-10-23 UTC

Related: existing Issues #154, #138 and #169. Status: REVIEW CANDIDATE / HOLD ACTIVATION / PRODUCTION NO-GO. This is a source review, not integration approval or a native build receipt. No framework was installed or run, no Apple login/SDK download was performed and no production API was connected.

## Decision

Continue the shared HUB 69 PWA for the first demo. SwiftUI with xtool is a feasible separate iOS proof of concept after a controlled toolchain/signing setup; it does not turn the current HTML/JS UI into SwiftUI. Keep MetaGPT out of the current Backend runtime: its Python constraints conflict with this sandbox and its tools can execute shell commands. A later worker must sit behind the existing Core authorization and audit boundary. Android should first use the same PWA; evaluate a Trusted Web Activity only after the approved HTTPS origin and Digital Asset Links exist. No additional Registry, identity namespace or HUB is needed.

## Versions and compatibility verified from official sources

| Project | Release observation | Source snapshot reviewed | Compatibility / limits |
|---|---|---|---|
| xtool | Latest GitHub release `1.23.0`, published 2026-10-22 21:29:36Z; release commit `e3ce2c402ec142d0d1bd0a0c9a20eb9c2ae8827c` | Main `952a7ffd435139f4f6f7a62951b0d14fda6f2fee` | Official Linux/WSL/macOS tool for building SwiftPM iOS apps, signing/installing, and Apple Developer Services. Release docs require Swift 6.4, usbmuxd and licensed Xcode 27 XIP; main docs have moved to Xcode 27.1. Do not mix main setup instructions with release evidence. |
| SwiftUI via xtool | Release DemoSimple imports SwiftUI, uses `@main App`, `WindowGroup`, `@State`, `Button` | Same xtool release commit | Demonstrates SwiftUI source support, not CFP+ runtime compatibility. Release package declares swift-tools 6.2 and iOS 17/macOS 14 for its own package/example; this is not proof that all future CFP+ APIs or devices are supported. |
| MetaGPT | Latest GitHub release `v0.8.1`, published 2024-04-22 10:56:23Z; release commit `c036574507e7616c02512e7c8ad88dd847783afa` | Main `11cdf466d042aece04fc6cfd13b28e1a70341b1f`, whose setup.py declares `1.0.0` | Main metadata/README require Python `>=3.9,<3.12`, Node and pnpm. The sandbox is Python 3.12.14, so direct installation is outside the declared Python range. Main's package version is not evidence of a GitHub 1.0.0 release or a tested published artifact. |

No `swift` or `xtool` executable was found on PATH. No iPhone, SDK, signing profile, native build, Android build, App Store/TestFlight or Play acceptance was tested. Apple SwiftUI documentation describes declarative views, controls, layout, localization/accessibility and integration with UIKit/AppKit/WatchKit; it does not establish Android support.

## License and dependency review

- xtool's root license is MIT: preserve copyright and license notices on copied/substantial distributed source. Its release lockfile pins 50 packages, including xtool-core 1.5.0 (`f867f9c2aea16ac78ca14d0d2f948b47db0732b4`), zsign 1.9.0 (`f6158be9e62a5ce2a53d72b1a6d880880da956c8`), Swift crypto/certificates/networking and subprocess packages. The pinned xtool-core and zsign root licenses were also checked as MIT. This is a partial dependency license review; all transitive notices, embedded native libraries, release binaries and downloaded SDK/macro artifacts remain unreviewed. MIT does not grant rights to redistribute Apple's SDK/Xcode or bypass its agreements.
- MetaGPT's main root license is MIT, with the same notice obligation. setup.py reads a large requirements list with both exact and open bounds (for example `pydantic>=2.5.3`, `playwright>=1.26`, `Pillow`, `fsspec`); a full reproducible lock/SBOM and transitive license/advisory scan were not generated. The Android assistant extra is an automation dependency set, not an Android app distribution framework.
- The open-source MetaGPT MIT license is not evidence of rights, privacy guarantees or enterprise terms for the separate hosted MGX/Atoms product advertised in its README. No hosted/enterprise component is approved or used. API providers, models, downloaded artifacts and third-party services retain their own terms.
- No vulnerability scan or security clearance is claimed. xtool SECURITY.md provides a GitHub private reporting route. MetaGPT SECURITY.md marks 0.7.x and earlier unsupported but does not establish a supported current release or patch SLA.

## Risk matrix and conditions before an isolated proof of concept

| Finding | Severity | Evidence / condition |
|---|---|---|
| Apple authentication and signing privilege | HIGH | xtool docs recommend App Store Connect Team Key with App Manager role for paid membership; password mode uses private Apple APIs. Use a separately approved signing environment and credential binding. Never collect Apple credentials in HUB 69 or store them in Git. Release 1.23.0 explicitly requires re-login for Apple ID authentication. |
| Untrusted agent tool execution / secret exposure | HIGH | MetaGPT main `metagpt/tools/libs/terminal.py` starts a persistent shell with `env=os.environ.copy()` and writes supplied command strings to stdin. Its two substring command exclusions are not a security sandbox. Run only in an isolated worker with no inherited production secrets, no host mounts and denied network by default; do not expose its generic terminal via Core. |
| Python and dependency drift | HIGH | Python 3.12.14 violates MetaGPT's declared upper bound. Pin a supported Python environment and exact framework commit, resolve/hash dependencies, check licenses/advisories, then run synthetic compatibility tests before integration. |
| SDK/toolchain and release/main drift | MEDIUM | xtool release uses Xcode 27 docs while main uses 27.1; release lock pins swift-collections 1.6.0 with a source comment about an older-OS crash in 1.7.0. Pin the release and SDK; retest required entitlements, macros and target OS rather than applying unreviewed main updates. |
| Confidential task or sponsor data reaching external models | HIGH | MetaGPT README config routes requests to configured model APIs. Use synthetic task content only until purpose-specific authorization, retention and redaction controls exist. Do not submit internal CFP+ documents as research or model prompts. |
| Android domain/app association | MEDIUM | Official TWA docs require same-developer website/app association through Digital Asset Links and explain that the host app cannot directly access browser cookies/localStorage. Association and installed-client behavior are untested; no DNS/asset association changes were made. |
| Build/physical-device acceptance missing | BLOCKED | No toolchain or devices here. Source feasibility is not native/PWA installation acceptance. |

## Proposed sandbox interface — not an implemented API

Reuse the existing Core client and versioned API contract. A future authenticated Core adapter accepts a task reference, tenant/principal from the verified session, idempotency key, allowed read capabilities and a bounded input artifact hash. Never accept client-asserted roles, approval or tenant authorization. Existing entity IDs, Parent, DID and Canonical links are read-only references, not worker-generated fields.

Core owns authorization, tenant isolation, task lifecycle, cancellation, deadlines, budgets and durable audit. A separate MetaGPT worker receives synthetic/minimal input and emits only bounded artifacts plus hashes and structured status (`proposed`, `running`, `ready_for_review`, `failed`, `cancelled`). Artifacts cannot grant approval or invoke registry/payment/deploy actions. Independent Review and Human Governance remain external to the worker. Retries reuse the task/idempotency key; rollback disables the adapter and cancels the worker without deleting audit receipts. Do not add an MCP endpoint merely because a framework is multi-agent: no reviewed MCP compatibility contract was established in this assessment.

Required tests before enabling that adapter: unauthenticated rejection; cross-tenant denial; duplicate idempotency behavior; explicit cancel/deadline/resource limit; denial of host/production network and secret access; malicious artifact/prompt unable to invoke tools or approval; bounded output; audit failure fails closed; restart/retry preserves receipts; UI cannot claim approved/live from a worker status. For native clients additionally test actual iPhone/Android auth return paths, session expiry, deep link back to HUB 69, offline/reconnect, accessibility, signing and HTTPS. These are pending tests, not PASS claims.

## Official source register

Sources fetched 2026-10-23 UTC using GitHub repository APIs/files and Firecrawl official-page retrieval. All source checks below are PASS for retrieval only.

1. [xtool release 1.23.0](https://github.com/xtool-org/xtool/releases/tag/1.23.0) and [release commit](https://github.com/xtool-org/xtool/commit/e3ce2c402ec142d0d1bd0a0c9a20eb9c2ae8827c).
2. [Release Linux/WSL setup](https://github.com/xtool-org/xtool/blob/e3ce2c402ec142d0d1bd0a0c9a20eb9c2ae8827c/Documentation/xtool.docc/Installation-Linux.md), [SwiftUI example](https://github.com/xtool-org/xtool/blob/e3ce2c402ec142d0d1bd0a0c9a20eb9c2ae8827c/Examples/DemoSimple/Sources/DemoSimple/App.swift), [Package.swift](https://github.com/xtool-org/xtool/blob/e3ce2c402ec142d0d1bd0a0c9a20eb9c2ae8827c/Package.swift), [lockfile](https://github.com/xtool-org/xtool/blob/e3ce2c402ec142d0d1bd0a0c9a20eb9c2ae8827c/Package.resolved).
3. [xtool MIT license](https://github.com/xtool-org/xtool/blob/952a7ffd435139f4f6f7a62951b0d14fda6f2fee/LICENSE.md), [security policy](https://github.com/xtool-org/xtool/blob/952a7ffd435139f4f6f7a62951b0d14fda6f2fee/SECURITY.md), [main setup](https://github.com/xtool-org/xtool/blob/952a7ffd435139f4f6f7a62951b0d14fda6f2fee/Documentation/xtool.docc/Installation-Linux.md).
4. [Pinned xtool-core license](https://github.com/xtool-org/xtool-core/blob/f867f9c2aea16ac78ca14d0d2f948b47db0732b4/LICENSE.md), [pinned zsign license](https://github.com/xtool-org/zsign/blob/f6158be9e62a5ce2a53d72b1a6d880880da956c8/LICENSE).
5. [MetaGPT release v0.8.1](https://github.com/FoundationAgents/MetaGPT/releases/tag/v0.8.1), [main snapshot](https://github.com/FoundationAgents/MetaGPT/tree/11cdf466d042aece04fc6cfd13b28e1a70341b1f), [README](https://github.com/FoundationAgents/MetaGPT#readme).
6. [MetaGPT setup.py](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/setup.py), [requirements](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/requirements.txt), [MIT license](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/LICENSE), [security policy](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/SECURITY.md), [terminal source](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/tools/libs/terminal.py).
7. [Apple SwiftUI documentation](https://developer.apple.com/documentation/swiftui).
8. [Chrome Trusted Web Activity overview](https://developer.chrome.com/docs/android/trusted-web-activity/overview). This page reports last updated 2020-02-04; use its architecture guidance without treating historical browser-version examples as current device support guarantees.

No upstream code was copied into CFP+, no framework activation was performed and no Stable ID, Parent, DID, Registry or Canonical was altered.
