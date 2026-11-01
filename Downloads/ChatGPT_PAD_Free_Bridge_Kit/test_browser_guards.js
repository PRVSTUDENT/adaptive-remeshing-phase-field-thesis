// Offline tests of actual userscript functions, without a ChatGPT browser.
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const source = fs.readFileSync(__dirname + '/chatgpt_direct_bridge.user.js', 'utf8');
const normalize = source.match(/function normalizeComposerText\(s\)\s*\{[\s\S]*?\n    \}/)[0];
const exact = source.match(/function composerContainsExactRequest\(text\)\s*\{[\s\S]*?\n    \}/)[0];
const prompt = '[BRIDGE_HANDOFF_ID=HND-SUP-test]\n' + 'a'.repeat(1000) + '\nEND';
let actual = prompt;
const check = vm.runInNewContext('(' + normalize + ', ' + exact + ')', {
    findComposer: () => ({ innerText: actual }),
    normalizeComposerText: s => String(s || '').replace(/\r\n?/g, '\n').replace(/\u00a0/g, ' ').trim()
});
assert(check(prompt));
actual = prompt.replace('a'.repeat(10), 'b'.repeat(10));
assert(!check(prompt), 'Same length/marker/tail must not conceal changed middle');
actual = prompt.slice(0, -1);
assert(!check(prompt), 'Truncated insertion must block send');
actual = prompt.replace(/\n/g, '\r\n');
assert(check(prompt), 'Equivalent line endings remain supported');
const clientLine = source.match(/const directClientId = .*;/)[0];
let seq = 0;
const context = { crypto: { randomUUID: () => 'document-' + (++seq) } };
const first = vm.runInNewContext(clientLine + '\ndirectClientId', context);
const second = vm.runInNewContext(clientLine + '\ndirectClientId', { crypto: context.crypto });
assert.notStrictEqual(first, second, 'Duplicated/reloaded documents must not inherit a claim');
console.log('PASS: exact prompt, changed middle, truncation, line endings, unique document claims (offline only).');
