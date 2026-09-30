import { promises as fs } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { parseMarkdownMetadata } from "./metadata.mjs";
import { validateRegistryFile } from "./rules.mjs";
import { buildMarkdownReport } from "./report.mjs";
import {
  CANONICAL_BLOCKED_RULES_001_016,
  normalizeAndValidateConfig
} from "./configIntegrity.mjs";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const validatorDir = path.resolve(scriptDir, "..");
const repoRoot = path.resolve(validatorDir, "../..");
const configPath = path.join(validatorDir, "config", "phase0.json");

async function exists(target) {
  try { await fs.access(target); return true; } catch { return false; }
}

async function walkMarkdown(dir) {
  const files = [];
  for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
    const target = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...await walkMarkdown(target));
    else if (entry.isFile() && entry.name.endsWith(".md")) files.push(target);
  }
  return files.sort();
}

function configFinding(message, evidence = undefined) {
  return {
    ruleId: "VAL-CONFIG-001",
    severity: "ERROR",
    file: "tools/validator/config/phase0.json",
    message,
    evidence,
    writePolicy: "no_autofix"
  };
}

function fallbackConfig() {
  return {
    repository: { owner: "charityfundplus", name: "CFP.plus", defaultBranch: "main" },
    paths: { registryDir: "registry", reportsDir: "reports" },
    rootExceptions: [],
    blockedSpecifications: [{ ...CANONICAL_BLOCKED_RULES_001_016 }]
  };
}

async function loadConfig(findings) {
  let rawText;
  try {
    rawText = await fs.readFile(configPath, "utf8");
  } catch (error) {
    findings.push(configFinding("Configuration file is missing.", { error: String(error) }));
    return fallbackConfig();
  }

  let parsed;
  try {
    parsed = JSON.parse(rawText);
  } catch (error) {
    findings.push(configFinding("Configuration file contains invalid JSON.", { error: String(error) }));
    return fallbackConfig();
  }

  return normalizeAndValidateConfig(
    parsed,
    rawText,
    (message, evidence) => findings.push(configFinding(message, evidence))
  );
}

async function main() {
  const findings = [];
  const config = await loadConfig(findings);

  const registryDir = path.join(repoRoot, config.paths?.registryDir || "registry");
  const files = await exists(registryDir) ? await walkMarkdown(registryDir) : [];
  if (!await exists(registryDir)) findings.push(configFinding("Missing required directory: registry/"));

  const registryIndex = new Map();
  for (const file of files) {
    const meta = parseMarkdownMetadata(await fs.readFile(file, "utf8"));
    if (meta.canonicalId) registryIndex.set(meta.canonicalId, { file, meta });
  }

  for (const file of files) {
    const relativeFile = path.relative(repoRoot, file).split(path.sep).join("/");
    const meta = parseMarkdownMetadata(await fs.readFile(file, "utf8"));
    findings.push(...validateRegistryFile({ file, relativeFile, meta, config, registryIndex }));
  }

  const counts = {
    error: findings.filter((item) => item.severity === "ERROR").length,
    warn: findings.filter((item) => item.severity === "WARN").length,
    info: findings.filter((item) => item.severity === "INFO").length
  };
  const report = {
    run: {
      timestamp: new Date().toISOString(),
      gitSha: process.env.GITHUB_SHA,
      gitRef: process.env.GITHUB_REF,
      workflow: process.env.GITHUB_WORKFLOW,
      phase: "phase0"
    },
    result: counts.error > 0 ? "FAIL" : "PASS",
    counts,
    blockedSpecifications: config.blockedSpecifications?.length
      ? config.blockedSpecifications
      : [{ ...CANONICAL_BLOCKED_RULES_001_016 }],
    findings
  };

  const reportsDir = path.join(repoRoot, config.paths?.reportsDir || "reports");
  await fs.mkdir(reportsDir, { recursive: true });
  await fs.writeFile(path.join(reportsDir, "validation-report.json"), `${JSON.stringify(report, null, 2)}\n`);
  await fs.writeFile(path.join(reportsDir, "validation-report.md"), buildMarkdownReport(report));

  console.log(`CFP+ Phase 0 validation: ${report.result} (${counts.error} errors, ${counts.warn} warnings)`);
  process.exitCode = counts.error > 0 ? 1 : 0;
}

await main();
