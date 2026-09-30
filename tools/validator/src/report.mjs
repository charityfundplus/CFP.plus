export function buildMarkdownReport(report) {
  const blocked = report.blockedSpecifications.map((spec) =>
    `- **${spec.specId}: ${spec.status}** — ${spec.note}\n  - Proposed path: \`${spec.proposedPath}\``
  ).join("\n");

  const rows = report.findings.map((item) =>
    `| ${item.severity} | ${item.ruleId} | \`${item.file}\` | ${item.message.replace(/\|/g, "\\|")} |`
  ).join("\n");

  return `# CFP+ Safe Framework Validator v0 — Phase 0\n\n## Result\n\n**${report.result}**\n\n| ERROR | WARN | INFO |\n|---:|---:|---:|\n| ${report.counts.error} | ${report.counts.warn} | ${report.counts.info} |\n\n## Blocked Specifications\n\n${blocked}\n\n> Không thể xác nhận PASS Rules 001–016 do thiếu canonical specification trong nhánh main.\n\n## Findings\n\n| Severity | Rule | File | Message |\n|---|---|---|---|\n${rows || "| INFO | — | — | No findings. |"}\n\n## Write Policy\n\nNo autofix. No direct registry edits. Canonical Locked and Governance Locked records remain report-only.\n`;
}
