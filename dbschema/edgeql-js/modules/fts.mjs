// GENERATED by @edgedb/generate v0.5.3

import * as $ from '../reflection.mjs';
import * as _ from '../imports.mjs';
const ElasticLanguage = $.makeType(_.spec, '68098129-5cf4-5272-8c64-2504e3dd95ad', _.syntax.literal);

const Language = $.makeType(_.spec, '4e291f3c-c871-56fb-b07a-0e841552c500', _.syntax.literal);

const LuceneLanguage = $.makeType(_.spec, '30696cb3-efd2-5146-8338-9ccc4ada0523', _.syntax.literal);

const PGLanguage = $.makeType(_.spec, '946d99dc-5330-5d27-9c74-3e8e522e0df3', _.syntax.literal);

const Weight = $.makeType(_.spec, '6ff6d8f7-ff4e-5653-af31-2976f6d87159', _.syntax.literal);

const document = $.makeType(_.spec, '82a03701-64a0-526d-9e43-397ce1e2022f', _.syntax.literal);

function with_options(...args) {
	const {
		returnType,
		cardinality,
		args: positionalArgs,
		namedArgs
	} = _.syntax.$resolveOverload('fts::with_options', args, _.spec, [
		{
			args: [{ typeId: '00000000-0000-0000-0000-000000000101', optional: false, setoftype: false, variadic: false }],
			namedArgs: {
				language: { typeId: '48896eaf-b8af-5f80-9073-0884475d6ee5', optional: false, setoftype: false, variadic: false },
				weight_category: { typeId: '6ff6d8f7-ff4e-5653-af31-2976f6d87159', optional: true, setoftype: false, variadic: false }
			},
			returnTypeId: '82a03701-64a0-526d-9e43-397ce1e2022f'
		}
	]);
	return _.syntax.$expressionify({
		__kind__: $.ExpressionKind.Function,
		__element__: returnType,
		__cardinality__: cardinality,
		__name__: 'fts::with_options',
		__args__: positionalArgs,
		__namedargs__: namedArgs
	});
}

function search(...args) {
	const {
		returnType,
		cardinality,
		args: positionalArgs,
		namedArgs
	} = _.syntax.$resolveOverload('fts::search', args, _.spec, [
		{
			args: [
				{ typeId: '00000000-0000-0000-0000-000000000003', optional: false, setoftype: false, variadic: false },
				{ typeId: '00000000-0000-0000-0000-000000000101', optional: false, setoftype: false, variadic: false }
			],
			namedArgs: {
				language: { typeId: '00000000-0000-0000-0000-000000000101', optional: true, setoftype: false, variadic: false },
				weights: { typeId: '2b65df4c-4942-59b1-8819-061ca68b2f4e', optional: true, setoftype: false, variadic: false }
			},
			returnTypeId: 'c13eb6f1-a05c-533f-bfe8-a50b1a077fd0',
			returnTypemod: 'OptionalType'
		}
	]);
	return _.syntax.$expressionify({
		__kind__: $.ExpressionKind.Function,
		__element__: returnType,
		__cardinality__: cardinality,
		__name__: 'fts::search',
		__args__: positionalArgs,
		__namedargs__: namedArgs
	});
}

export { ElasticLanguage, Language, LuceneLanguage, PGLanguage, Weight, document };

const __defaultExports = {
	ElasticLanguage: ElasticLanguage,
	Language: Language,
	LuceneLanguage: LuceneLanguage,
	PGLanguage: PGLanguage,
	Weight: Weight,
	document: document,
	with_options: with_options,
	search: search
};
export default __defaultExports;
