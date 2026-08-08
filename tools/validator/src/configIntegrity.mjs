export const CANONICAL_BLOCKED_RULES_001_016 = Object.freeze({
  specId: "VALIDATION_RULES_001_016",
  status: "SOURCE_REQUIRED",
  note: "CANONICAL SPECIFICATION NOT YET LOCATED IN MAIN",
  proposedPath: "governance/validation/VALIDATION_SCRIPT_SPECIFICATION_v1.2.md"
});

function isNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function cloneCanonicalBlockedSpec() {
  return { ...CANONICAL_BLOCKED_RULES_001_016 };
}

function skipWhitespace(text, state) {
  while (/\s/.test(text[state.i] ?? "")) state.i += 1;
}

function parseStringToken(text, state) {
  if (text[state.i] !== '"') throw new Error(`Expected string at offset ${state.i}`);
  const start = state.i;
  state.i += 1;
  let escaped = false;
  while (state.i < text.length) {
    const ch = text[state.i++];
    if (escaped) { escaped = false; continue; }
    if (ch === "\\") { escaped = true; continue; }
    if (ch === '"') return JSON.parse(text.slice(start, state.i));
  }
  throw new Error(`Unterminated string at offset ${start}`);
}

function parsePrimitive(text, state) {
  const start = state.i;
  while (state.i < text.length && !/[\s,}\]]/.test(text[state.i])) state.i += 1;
  const token = text.slice(start, state.i);
  if (!/^(true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)$/.test(token)) {
    throw new Error(`Invalid JSON token at offset ${start}`);
  }
}

function parseValue(text, state, path, duplicates) {
  skipWhitespace(text, state);
  const ch = text[state.i];
  if (ch === "{") return parseObject(text, state, path, duplicates);
  if (ch === "[") return parseArray(text, state, path, duplicates);
  if (ch === '"') { parseStringToken(text, state); return; }
  parsePrimitive(text, state);
}

function parseArray(text, state, path, duplicates) {
  state.i += 1;
  skipWhitespace(text, state);
  let index = 0;
  if (text[state.i] === "]") { state.i += 1; return; }
  while (state.i < text.length) {
    parseValue(text, state, `${path}[${index}]`, duplicates);
    index += 1;
    skipWhitespace(text, state);
    if (text[state.i] === "]") { state.i += 1; return; }
    if (text[state.i] !== ",") throw new Error(`Expected comma in array at offset ${state.i}`);
    state.i += 1;
  }
  throw new Error("Unterminated array");
}

function parseObject(text, state, path, duplicates) {
  state.i += 1;
  skipWhitespace(text, state);
  const seen = new Set();
  if (text[state.i] === "}") { state.i += 1; return; }
  while (state.i < text.length) {
    skipWhitespace(text, state);
    const key = parseStringToken(text, state);
    const keyPath = path ? `${path}.${key}` : key;
    if (seen.has(key)) duplicates.push(keyPath);
    seen.add(key);
    skipWhitespace(text, state);
    if (text[state.i] !== ":") throw new Error(`Expected colon at offset ${state.i}`);
    state.i += 1;
    parseValue(text, state, keyPath, duplicates);
    skipWhitespace(text, state);
    if (text[state.i] === "}") { state.i += 1; return; }
    if (text[state.i] !== ",") throw new Error(`Expected comma in object at offset ${state.i}`);
    state.i += 1;
  }
  throw new Error("Unterminated object");
}

export function detectDuplicateJsonKeys(rawText) {
  const state = { i: 0 };
  const duplicates = [];
  parseValue(rawText, state, "", duplicates);
  skipWhitespace(rawText, state);
  if (state.i !== rawText.length) throw new Error(`Unexpected content at offset ${state.i}`);
  return duplicates;
}

export function normalizeAndValidateConfig(config, rawText, addError) {
  try {
    const duplicates = detectDuplicateJsonKeys(rawText);
    if (duplicates.length > 0) addError("Duplicate JSON keys are not allowed.", { duplicateKeys: duplicates });
  } catch (error) {
    addError("Configuration JSON structural scan failed.", { error: String(error) });
  }

  if (!config || typeof config !== "object" || Array.isArray(config)) {
    addError("Configuration root must be an object.");
    config = {};
  }

  if (!config.repository || typeof config.repository !== "object" || Array.isArray(config.repository)) {
    addError("repository must be an object.");
    config.repository = {};
  }
  for (const key of ["owner", "name", "defaultBranch"]) {
    if (!isNonEmptyString(config.repository[key])) addError(`repository.${key} must be a non-empty string.`);
  }

  if (!config.paths || typeof config.paths !== "object" || Array.isArray(config.paths)) {
    addError("paths must be an object.");
    config.paths = {};
  }
  for (const key of ["registryDir", "reportsDir"]) {
    if (!isNonEmptyString(config.paths[key])) addError(`paths.${key} must be a non-empty string.`);
  }

  if (!Array.isArray(config.rootExceptions)) {
    addError("rootExceptions must be an array of non-empty strings.");
    config.rootExceptions = [];
  } else {
    config.rootExceptions.forEach((item, index) => {
      if (!isNonEmptyString(item)) addError(`rootExceptions[${index}] must be a non-empty string.`);
    });
    config.rootExceptions = config.rootExceptions.filter(isNonEmptyString);
  }

  let blocked = config.blockedSpecifications;
  if (!Array.isArray(blocked)) {
    addError("blockedSpecifications must be an array.");
    blocked = [];
  }

  const validItems = [];
  blocked.forEach((item, index) => {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      addError(`blockedSpecifications[${index}] must be an object.`);
      return;
    }
    const required = ["specId", "status", "note", "proposedPath"];
    let valid = true;
    for (const key of required) {
      if (!isNonEmptyString(item[key])) {
        addError(`blockedSpecifications[${index}].${key} must be a non-empty string.`);
        valid = false;
      }
    }
    if (item.status !== "SOURCE_REQUIRED") {
      addError(`blockedSpecifications[${index}].status must equal SOURCE_REQUIRED.`);
      valid = false;
    }
    if (valid) validItems.push({ ...item });
  });

  const canonicalValid = validItems.some((item) =>
    item.specId === CANONICAL_BLOCKED_RULES_001_016.specId &&
    item.status === CANONICAL_BLOCKED_RULES_001_016.status &&
    item.note === CANONICAL_BLOCKED_RULES_001_016.note &&
    item.proposedPath === CANONICAL_BLOCKED_RULES_001_016.proposedPath
  );
  if (!canonicalValid) {
    addError("Canonical blocked specification VALIDATION_RULES_001_016 is missing or invalid; fallback inserted.");
    validItems.push(cloneCanonicalBlockedSpec());
  }

  config.blockedSpecifications = validItems;
  return config;
}
