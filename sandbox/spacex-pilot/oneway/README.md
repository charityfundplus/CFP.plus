# Synthetic one-way experiment — DRAFT

Continues existing sandbox/spacex-pilot and Draft PR #184. No Registry data or production files are changed. No real SpaceX API/account/affiliation. No REA installation or Clean Room independence claim: this is direct implementation of the supplied draft.

Node 24 with node:sqlite, standard library only. Tests are self-contained and need no demo, checked-in SQLite or prior permission receipt:

```sh
node --test --test-isolation=none --test-reporter=tap test.mjs
```

Each test run generates fixtures and SQLite in unique OS temporary directories, cleans them up, and leaves the historical evidence/ directory untouched. The loopback HTTP test needs permission to listen on 127.0.0.1; denial is a failure, not a silent pass. --test-isolation=none also works on executors that restrict child test processes. The former E3 receipt dependency is replaced by a fresh source/no-writeback test. A separate Node filesystem permission probe remains an independent command, not something inferred from old evidence.

For a manual demo, choose a fresh output directory outside the historical evidence/ directory:

```sh
run_dir=$(mktemp -d /tmp/cfp-oneway-demo.XXXXXX)
node demo.mjs "$run_dir" > "$run_dir/demo.json"
node --permission --allow-fs-read="$PWD/permission-probe.mjs" --allow-fs-read="$run_dir/synthetic-input.json" permission-probe.mjs "$run_dir/synthetic-input.json" > "$run_dir/isolation.json"
```

The demo function accepts an injected clock for deterministic tests; CLI uses current UTC. Synthetic fixture dates and IDs are not real event identities. makeHandler(outputDirectory) serves a chosen generated export; CLI server.mjs still serves historical evidence/ by default, LOCAL ONLY. No public preview or live CFP+ feed is implied.

Run both integrated suites from repository root:

```sh
PILOT_SOCKET_TEST=1 node --test --test-isolation=none --test-reporter=tap sandbox/spacex-pilot/test.mjs sandbox/spacex-pilot/oneway/test.mjs
node sandbox/spacex-pilot/check-ui.cjs
```

The optional UI check requires Playwright and Chromium. It creates a fresh output directory, checks pilot and HUB 69 at 375/390/1440 px, and saves screenshots and results there. This is Chromium viewport testing, not physical iPhone Safari.

The offline Registry importer now exposes Importer.fromSnapshot(bytes, approvedIds), which verifies the reviewed snapshot SHA-256 before construction; the read-only preview also verifies bytes before serving registry.json. This reuses #183's byte-integrity approach. The fixture contains ChatGPT/OpenAI and ancestor references, not loaded country ancestors, a SpaceX allocation or approved live-feed authentication. The persistent synthetic status adapter remains separate from the Registry projection; these are experiments within #184, not a production synchronization service.

See SPEC.md for chosen semantics and E1–E5. REPORT.md records actual execution and missing evidence. ReviewSI/SecuritySI acceptance is PENDING; do not merge or deploy.
