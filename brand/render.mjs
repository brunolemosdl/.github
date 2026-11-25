// Render the PNGs of a brand kit written by brandkit.write_kit, with resvg.
//
//   node render.mjs <kit folder> [prefix]
//
// resvg comes from @resvg/resvg-js; set RESVG to the module path when it is not installed next
// to this file (in Bruno's WSL it is in ~/workspace/forja/app/node_modules/@resvg/resvg-js).
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { homedir } from 'node:os';

const require = createRequire(import.meta.url);
const mod = process.env.RESVG || `${homedir()}/workspace/forja/app/node_modules/@resvg/resvg-js`;
const { Resvg } = require(mod);
const [dir, prefix = ''] = process.argv.slice(2);
const at = (f) => `${dir}/${prefix}${f}`;
const png = (src, width, dst) => {
	if (!existsSync(at(src))) return;
	writeFileSync(at(dst), new Resvg(readFileSync(at(src), 'utf8'), { fitTo: { mode: 'width', value: width } }).render().asPng());
};
const width = (f) => Number(readFileSync(at(f), 'utf8').match(/viewBox="0 0 (\d+)/)[1]);

png('mark.svg', 1024, 'mark.png');
png('avatar.svg', 512, 'avatar.png');
for (const s of [16, 32, 48]) png('mark-small.svg', s, `favicon-${s}.png`);
for (const s of [180, 192, 512]) png('app-icon.svg', s, `app-icon-${s}.png`);
for (const f of ['lockup-horizontal', 'lockup-stacked'])
	if (existsSync(at(`${f}.svg`))) png(`${f}.svg`, width(`${f}.svg`) * 2, `${f}.png`);
console.log('rendered', dir);
