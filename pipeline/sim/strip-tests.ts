/** Remove named tests from a test file, so a mutant kill can be attributed to them. */
import { readFileSync, writeFileSync } from 'node:fs';
const [file, ...names] = process.argv.slice(2);
let s = readFileSync(file!, 'utf8');
for (const n of names) {
  const i = s.indexOf(n);
  if (i < 0) { console.log(`MISS ${n}`); continue; }
  const start = s.lastIndexOf('test(', i);
  const end = s.indexOf('\n});', i);
  if (start < 0 || end < 0) { console.log(`UNBOUNDED ${n}`); continue; }
  s = s.slice(0, start) + s.slice(end + 4);
  console.log(`stripped: ${n}`);
}
writeFileSync(file!, s);
