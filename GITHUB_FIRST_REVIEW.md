# Website code audit changes

Source: charityfundplus/CFP.plus main 835616308111f6851c0387fa9f5eda60c9ffa624. This branch is a review candidate, not deployed code.

- Fix missing /assets/style.css on 267 and 2676 to existing /styles.css.
- Unknown numeric routes remain accessible through Nginx fallback but no longer assert formula-derived Parent, entity binding or ACTIVE status. Unknown/non-numeric identity views require Registry review; generated slots without registry records do not become links or identities.
- Registry files, protected 691141 data, existing DID assignments and chapter records are unchanged. Source-record Parent fields are read-only; conflicting records still require independent Human Governance review.
- Exclude Git metadata, caches and secret files from image context; exclude them from commits.
- Pass pilot secret checks through env vars instead of GitHub expression interpolation in shell.

Remaining: 582 numeric directory navigation references retain trailing slashes for historical compatibility; canonical identity strings must use https://cfp.plus/{ASCII digits}. 52 fallback targets do not prove registered identities. Five identical-file groups include reserved templates/empty files; no identity pages are deleted. Core P0 pair registry is not installed in this Website: approve versioned read-only Backend integration and routing before declaring Website↔Backend parity. No parallel data authority is created.

Verification is orchestrated by the gateway GitHub-first branch; its single final HEAD pins this Website commit as a component dependency and reruns Website CTTTC, Unicode and browser tests. No earlier run proves that final HEAD. No Merge, Deploy, Canonical Lock, new DID or Parent binding.
