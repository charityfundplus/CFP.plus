import path from "node:path";

export function parseMarkdownMetadata(markdown) {
  const lines = markdown.split(/\r?\n/);
  const fields = new Map();
  const pattern = /^\s*(?:\*\*)?([A-Za-z][A-Za-z0-9 /_-]*?)(?:\*\*)?\s*:\s*(?:\*\*)?(.+?)(?:\*\*)?\s*$/;

  for (const line of lines) {
    const match = line.match(pattern);
    if (!match) continue;
    const key = match[1].trim().toLowerCase();
    const value = match[2].trim().replace(/\*\*$/, "").trim();
    fields.set(key, value);
  }

  let canonicalLink;
  const section = lines.findIndex((line) => /^##\s+1\.\s+Canonical Link\s*$/i.test(line.trim()));
  if (section >= 0) {
    for (let i = section + 1; i < lines.length; i += 1) {
      if (/^##\s+/.test(lines[i])) break;
      const url = lines[i].match(/https:\/\/github\.com\/[^\s)>]+/i)?.[0];
      if (url) {
        canonicalLink = url.replace(/[.,;]+$/, "");
        break;
      }
    }
  }

  const parentHubRaw = fields.get("parent hub");
  const lifecycleStatus = fields.get("lifecycle status");
  const governanceStatus = fields.get("governance status");

  return {
    canonicalId: fields.get("canonical id"),
    entityName: fields.get("entity name"),
    entityType: fields.get("entity type"),
    parentHubRaw,
    parentHubId: parentHubRaw?.match(/^(\d+)\b/)?.[1],
    lifecycleStatus,
    visibility: fields.get("visibility"),
    canonicalLink,
    canonicalLocked: /^canonical locked$/i.test(lifecycleStatus ?? "") || /^canonical locked$/i.test(governanceStatus ?? ""),
    governanceLocked: /^governance locked$/i.test(lifecycleStatus ?? "") || /^governance locked$/i.test(governanceStatus ?? "")
  };
}

export function parentName(raw) {
  return raw?.replace(/^\d+\s*(?:[•|:-])?\s*/, "").trim() || undefined;
}

export function filenameId(file) {
  return path.basename(file, ".md");
}
