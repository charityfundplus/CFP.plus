import path from "node:path";
import { filenameId, parentName } from "./metadata.mjs";

function makeFinding(ruleId, severity, file, message, extra = {}) {
  return { ruleId, severity, file, message, writePolicy: "no_autofix", ...extra };
}

export function validateRegistryFile({ file, relativeFile, meta, config, registryIndex }) {
  const findings = [];
  const locked = Boolean(meta.canonicalLocked || meta.governanceLocked);
  const lock = { governanceLock: locked };
  const base = filenameId(file);

  if (!meta.canonicalId) {
    findings.push(makeFinding("VAL-ID-001", "WARN", relativeFile, "Missing Canonical ID.", lock));
  } else if (!/^\d+$/.test(meta.canonicalId)) {
    findings.push(makeFinding("VAL-ID-003", "ERROR", relativeFile, "Canonical ID must contain digits only.", { canonicalId: meta.canonicalId, ...lock }));
  } else if (base !== meta.canonicalId) {
    findings.push(makeFinding("VAL-ID-002", "ERROR", relativeFile, "Filename does not match Canonical ID.", {
      canonicalId: meta.canonicalId,
      evidence: { filenameId: base, canonicalId: meta.canonicalId },
      ...lock
    }));
  }

  const expectedLink = `https://github.com/${config.repository.owner}/${config.repository.name}/blob/${config.repository.defaultBranch}/${relativeFile}`;
  if (!meta.canonicalLink) {
    findings.push(makeFinding("VAL-LINK-001", "ERROR", relativeFile, "Missing Canonical Link under section '## 1. Canonical Link'.", lock));
  } else if (meta.canonicalLink !== expectedLink) {
    findings.push(makeFinding("VAL-LINK-002", "ERROR", relativeFile, "Canonical Link does not match repository path on main.", {
      evidence: { canonicalLink: meta.canonicalLink, expected: expectedLink },
      ...lock
    }));
  }

  const childId = meta.canonicalId;
  const rootException = childId ? config.rootExceptions.includes(childId) : false;
  if (!rootException) {
    if (!meta.parentHubRaw) {
      findings.push(makeFinding("VAL-PARENT-001", "ERROR", relativeFile, "Missing Parent Hub for non-exception registry entity.", { canonicalId: childId, ...lock }));
    } else if (!childId || !/^\d+$/.test(childId) || !meta.parentHubId || !/^\d+$/.test(meta.parentHubId)) {
      findings.push(makeFinding("VAL-PARENT-002", "ERROR", relativeFile, "Invalid Parent Hub format or non-numeric Canonical ID.", {
        canonicalId: childId,
        evidence: { parentHubRaw: meta.parentHubRaw },
        ...lock
      }));
    } else {
      const expectedParentId = childId.slice(0, -1);
      if (!expectedParentId || meta.parentHubId !== expectedParentId) {
        findings.push(makeFinding("VAL-PARENT-004", "ERROR", relativeFile, "Direct Parent Prefix Mismatch.", {
          canonicalId: childId,
          evidence: { parentHubId: meta.parentHubId, expectedDirectParentId: expectedParentId },
          ...lock
        }));
      } else {
        const parent = registryIndex.get(meta.parentHubId);
        if (!parent) {
          findings.push(makeFinding("VAL-PARENT-003", "WARN", relativeFile, "Parent record not located.", {
            canonicalId: childId,
            evidence: { parentHubId: meta.parentHubId, marker: "PARENT_RECORD_NOT_LOCATED" },
            ...lock
          }));
        } else {
          if (filenameId(parent.file) !== meta.parentHubId) {
            findings.push(makeFinding("VAL-PARENT-006", "ERROR", relativeFile, "Parent ID and parent filename mismatch.", { canonicalId: childId, ...lock }));
          }
          const declared = parentName(meta.parentHubRaw);
          if (declared && parent.meta.entityName && declared !== parent.meta.entityName) {
            findings.push(makeFinding("VAL-PARENT-005", "WARN", relativeFile, "Parent Name Mismatch (Parent ID is correct).", {
              canonicalId: childId,
              evidence: { declaredParentName: declared, recordedParentName: parent.meta.entityName },
              ...lock
            }));
          }
        }
      }
    }
  }

  if (!meta.lifecycleStatus) findings.push(makeFinding("VAL-META-001", "WARN", relativeFile, "Missing Lifecycle Status.", lock));
  if (!meta.visibility) findings.push(makeFinding("VAL-META-002", "WARN", relativeFile, "Missing Visibility.", lock));
  return findings;
}
