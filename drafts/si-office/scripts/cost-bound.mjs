import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';

const groups = ['F', 'U', 'D', 'R', 'S'];
const cents = value => Number.isSafeInteger(value) && value >= 0;
const nonempty = value => typeof value === 'string' && value.trim().length > 0;
const reference = value => {
  if (!nonempty(value)) return false;
  try { const u = new URL(value); return u.protocol === 'https:' && !u.username && !u.password; }
  catch { return false; }
};

// Offline arithmetic only. References are not fetched or authenticated.
// F includes gross fixed charges; U accrued/pending not already in F;
// D bounded incremental charges during closure; R residual not in F/U/D;
// S quantified uncertainty. Every component must use one gross USD period.
export function costBound(input) {
  if (!input || input.currency !== 'USD' || input.basis !== 'grossUSD'
      || !nonempty(input.period) || !nonempty(input.scope)
      || input.nonOverlapping !== true || !reference(input.allocationEvidenceRef)
      || !cents(input.targetCents) || !Array.isArray(input.components)) {
    throw Error('COST_SCOPE_REQUIRED');
  }
  const seen = new Set(), unknown = [], totals = {};
  for (const row of input.components) {
    if (!row || !groups.includes(row.group) || seen.has(row.group)) throw Error('GROUP_DUPLICATE_OR_INVALID');
    seen.add(row.group);
    if (row.cents === null) { unknown.push(row.group); totals[row.group] = null; continue; }
    if (!cents(row.cents) || !reference(row.evidenceRef)) throw Error('AMOUNT_OR_REFERENCE_INVALID');
    totals[row.group] = row.cents;
  }
  for (const group of groups) if (!seen.has(group)) { unknown.push(group); totals[group] = null; }
  let total = 0;
  for (const value of Object.values(totals)) {
    if (value === null) continue;
    total += value;
    if (!cents(total)) throw Error('TOTAL_UNSAFE');
  }
  const boundCents = unknown.length ? null : total;
  return {
    schemaVersion: 1, mode: 'OFFLINE ARITHMETIC / REFERENCES UNVERIFIED',
    currency: 'USD', basis: 'grossUSD', period: input.period, scope: input.scope,
    targetCents: input.targetCents, totals, unknown,
    boundCents, knownSubtotalCents: total,
    withinTargetArithmetic: boundCents === null ? null : boundCents <= input.targetCents,
    headroomCents: boundCents === null ? null : input.targetCents - boundCents,
    evidenceAuthenticated: false, hardCapVerified: false, activationAllowed: false,
    checkoutPerformed: false, providerCalls: 0,
  };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try { console.log(JSON.stringify(costBound(JSON.parse(readFileSync(process.argv[2], 'utf8'))), null, 2)); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
