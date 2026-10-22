// This module has no side effects. build.mjs writes the same tokens to every UI bundle.
export function tokenCSS(tokens) {
  if (!/^\d+\.\d+\.\d+$/.test(tokens.version)) throw Error('INVALID_TOKEN_VERSION');
  const entries = Object.entries(tokens.cssVariables);
  for (const [name, value] of entries) {
    if (!/^--[a-z][a-z0-9-]*$/.test(name) || typeof value !== 'string' || /[{};<>]/.test(value)) {
      throw Error('INVALID_CSS_TOKEN');
    }
  }
  return `/* HUB 69 Design System ${tokens.version}; generated from design-tokens.json */\n:root{\n${entries.map(([k,v])=>`  ${k}: ${v};`).join('\n')}\n}\n`;
}
