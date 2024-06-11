// GENERATED by @edgedb/generate v0.5.3

export * from './external.mjs';
export { createClient } from 'edgedb';
import * as $ from './reflection.mjs';
import * as $syntax from './syntax.mjs';
import * as $op from './operators.mjs';
import _std from './modules/std.mjs';
import _cal from './modules/cal.mjs';
import _cfg from './modules/cfg.mjs';
import _fts from './modules/fts.mjs';
import _schema from './modules/schema.mjs';
import _sys from './modules/sys.mjs';
import _default from './modules/default.mjs';
import _math from './modules/math.mjs';

const ExportDefault = {
	..._std,
	..._default,
	...$.util.omitDollarPrefixed($syntax),
	...$op,
	std: _std,
	cal: _cal,
	cfg: _cfg,
	fts: _fts,
	schema: _schema,
	sys: _sys,
	default: _default,
	math: _math
};
const Cardinality = $.Cardinality;

export default ExportDefault;
export { Cardinality };
