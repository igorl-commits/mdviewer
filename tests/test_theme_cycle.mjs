// Theme-cycle logic test. Extracts effectiveTheme()/nextTheme() from the JS
// template in template.py and verifies no click is ever a visual no-op.
// Run: node tests/test_theme_cycle.mjs
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const src = readFileSync(join(dirname(fileURLToPath(import.meta.url)), '..', 'template.py'), 'utf8');
const m = src.match(/\/\/ THEME-CYCLE-LOGIC-START([\s\S]*?)\/\/ THEME-CYCLE-LOGIC-END/);
if (!m) { console.error('FAIL: theme-cycle logic markers not found in template.py'); process.exit(1); }

let failures = 0;
function check(name, actual, expected) {
  if (actual === expected) { console.log(`ok   ${name}`); }
  else { console.error(`FAIL ${name}: got ${actual}, expected ${expected}`); failures++; }
}

function makeScope(systemDark) {
  // The extracted JS reads `window.matchMedia` and `currentTheme` from scope.
  const body = `
    const window = { matchMedia: q => ({ matches: ${systemDark} }) };
    let currentTheme = theme;
    ${m[1]}
    return { eff: effectiveTheme(theme), next: nextTheme() };
  `;
  return new Function('theme', body);
}

for (const systemDark of [true, false]) {
  const run = makeScope(systemDark);
  const sys = systemDark ? 'dark' : 'light';
  const label = `system=${sys}`;

  for (const theme of ['dark', 'light', 'system']) {
    const { eff, next } = run(theme);
    // effectiveTheme resolves 'system' to the OS appearance
    check(`${label} effective(${theme})`, eff, theme === 'system' ? sys : theme);
    // the cardinal rule: the next theme must look different from the current one
    const nextEff = run(next).eff;
    if (nextEff === eff) { console.error(`FAIL ${label} next(${theme})=${next} is a visual no-op`); failures++; }
    else { console.log(`ok   ${label} next(${theme})=${next} visibly changes`); }
  }

  // exact transitions
  check(`${label} next(dark)`, run('dark').next, 'light');
  check(`${label} next(light)`, run('light').next, systemDark ? 'system' : 'dark');
  check(`${label} next(system)`, run('system').next, systemDark ? 'light' : 'dark');
}

if (failures) { console.error(`\n${failures} failure(s)`); process.exit(1); }
console.log('\nall theme-cycle tests passed');
