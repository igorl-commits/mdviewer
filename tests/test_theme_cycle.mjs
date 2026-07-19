// App-theme smoke test. Verifies every THEME_LIST key has chrome CSS and HLJS CSS
// wired in template.py (no light/dark/system cycle anymore).
// Run: node tests/test_theme_cycle.mjs
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const src = readFileSync(join(dirname(fileURLToPath(import.meta.url)), '..', 'template.py'), 'utf8');

const expected = [
  'github-dark',
  'github',
  'dracula',
  'monokai',
  'nord',
  'atom-one-dark',
  'solarized-dark',
  'vs2015',
];

let failures = 0;
function check(name, ok, detail = '') {
  if (ok) console.log(`ok   ${name}`);
  else { console.error(`FAIL ${name}${detail ? ': ' + detail : ''}`); failures++; }
}

// No legacy light/dark/system app-theme cycle
check('no effectiveTheme()', !src.includes('function effectiveTheme'));
check('no nextTheme()', !src.includes('function nextTheme'));
check('no prefers-color-scheme listener for system theme',
  !src.includes("currentTheme === 'system'"));
check('no Switch to Light menu', !src.includes('Switch to Light'));
check('no Follow System menu', !src.includes('Follow System'));

for (const key of expected) {
  check(`chrome CSS [data-theme="${key}"]`, src.includes(`[data-theme="${key}"]`));
}

check('setTheme function present', src.includes('function setTheme(key)'));
check('menu label Theme (not Syntax Theme)', src.includes("textContent = 'Theme'"));
check('persists theme only', src.includes('save_config({theme: currentTheme})'));

if (failures) {
  console.error(`\n${failures} failure(s)`);
  process.exit(1);
}
console.log('\nall theme tests passed');
