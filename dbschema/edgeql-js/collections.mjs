// GENERATED by @edgedb/generate v0.5.3

import { Cardinality, ExpressionKind, TypeKind } from 'edgedb/dist/reflection/index.js';
import { cardutil } from './cardinality.mjs';
import { $expressionify } from './path.mjs';
import { literalToTypeSet } from './castMaps.mjs';
const indexSliceRegx = /^(-?\d+)(?:(:)(-?\d+)?)?|:(-?\d+)$/;
const arrayLikeProxyHandlers = {
	get(target, prop, proxy) {
		const match = typeof prop === 'string' ? prop.match(indexSliceRegx) : null;
		if (match) {
			const start = match[1];
			const end = match[3] ?? match[4];
			const isIndex = start && !match[2];
			return $expressionify({
				__kind__: ExpressionKind.Operator,
				__element__: target.__element__.__kind__ === TypeKind.array && isIndex ? target.__element__.__element__ : target.__element__,
				__cardinality__: target.__cardinality__,
				__name__: '[]',
				__opkind__: 'Infix',
				__args__: [
					proxy,
					isIndex ? literalToTypeSet(Number(start)) : [start && literalToTypeSet(Number(start)), end && literalToTypeSet(Number(end))]
				]
			});
		}
		return target[prop];
	}
};
function arrayLikeIndex(index) {
	const indexTypeSet = literalToTypeSet(index);
	return $expressionify({
		__kind__: ExpressionKind.Operator,
		__element__: this.__element__.__kind__ === TypeKind.array ? this.__element__.__element__ : this.__element__,
		__cardinality__: cardutil.multiplyCardinalities(this.__cardinality__, indexTypeSet.__cardinality__),
		__name__: '[]',
		__opkind__: 'Infix',
		__args__: [this, indexTypeSet]
	});
}
function arrayLikeSlice(start, end) {
	const startTypeSet = start && literalToTypeSet(start);
	const endTypeSet = end && literalToTypeSet(end);
	return $expressionify({
		__kind__: ExpressionKind.Operator,
		__element__: this.__element__,
		__cardinality__: cardutil.multiplyCardinalities(
			cardutil.multiplyCardinalities(this.__cardinality__, startTypeSet?.__cardinality__ ?? Cardinality.One),
			endTypeSet?.__cardinality__ ?? Cardinality.One
		),
		__name__: '[]',
		__opkind__: 'Infix',
		__args__: [this, [startTypeSet, endTypeSet]]
	});
}
export function $arrayLikeIndexify(_expr) {
	if (
		_expr.__element__.__kind__ === TypeKind.array ||
		(_expr.__element__.__kind__ === TypeKind.scalar && (_expr.__element__.__name__ === 'std::str' || _expr.__element__.__name__ === 'std::bytes'))
	) {
		const expr = new Proxy(_expr, arrayLikeProxyHandlers);
		expr.index = arrayLikeIndex.bind(expr);
		expr.slice = arrayLikeSlice.bind(expr);
		return expr;
	}
	return _expr;
}
export function array(arg) {
	if (Array.isArray(arg)) {
		const items = arg.map((a) => literalToTypeSet(a));
		return $expressionify({
			__kind__: ExpressionKind.Array,
			__cardinality__: cardutil.multiplyCardinalitiesVariadic(items.map((item) => item.__cardinality__)),
			__element__: {
				__kind__: TypeKind.array,
				__name__: `array<${items[0].__element__.__name__}>`,
				__element__: items[0].__element__
			},
			__items__: items
		});
	}
	if (arg.__kind__) {
		return {
			__kind__: TypeKind.array,
			__name__: `array<${arg.__name__}>`,
			__element__: arg
		};
	}
	throw new Error('Invalid array input.');
}
const tupleProxyHandlers = {
	get(target, prop, proxy) {
		const type = target.__element__;
		const items = type.__kind__ === TypeKind.tuple ? type.__items__ : type.__kind__ === TypeKind.namedtuple ? type.__shape__ : null;
		return items?.hasOwnProperty(prop) ? tuplePath(proxy, items[prop], prop) : target[prop];
	}
};
export function $tuplePathify(expr) {
	if (expr.__element__.__kind__ !== TypeKind.tuple && expr.__element__.__kind__ !== TypeKind.namedtuple) {
		return expr;
	}
	return new Proxy(expr, tupleProxyHandlers);
}
function tuplePath(parent, itemType, index) {
	return $expressionify({
		__kind__: ExpressionKind.TuplePath,
		__element__: itemType,
		__cardinality__: parent.__cardinality__,
		__parent__: parent,
		__index__: index
	});
}
function makeTupleType(name, items) {
	return {
		__kind__: TypeKind.tuple,
		__name__: name,
		__items__: items
	};
}
const typeKinds = new Set(Object.values(TypeKind));
export function tuple(input) {
	if (Array.isArray(input)) {
		if (input.every((item) => typeKinds.has(item.__kind__))) {
			const typeItems = input;
			const typeName = `tuple<${typeItems.map((item) => item.__name__).join(', ')}>`;
			return makeTupleType(typeName, typeItems);
		}
		const items = input.map((item) => literalToTypeSet(item));
		const name = `tuple<${items.map((item) => item.__element__.__name__).join(', ')}>`;
		return $expressionify({
			__kind__: ExpressionKind.Tuple,
			__element__: makeTupleType(
				name,
				items.map((item) => item.__element__)
			),
			__cardinality__: cardutil.multiplyCardinalitiesVariadic(items.map((i) => i.__cardinality__)),
			__items__: items
		});
	} else {
		if (Object.values(input).every((el) => typeKinds.has(el.__kind__))) {
			const typeName = `tuple<${Object.entries(input)
				.map(([key, val]) => `${key}: ${val.__name__}`)
				.join(', ')}>`;
			return {
				__kind__: TypeKind.namedtuple,
				__name__: typeName,
				__shape__: input
			};
		}
		const exprShape = {};
		const typeShape = {};
		for (const [key, val] of Object.entries(input)) {
			const typeSet = literalToTypeSet(val);
			exprShape[key] = typeSet;
			typeShape[key] = typeSet.__element__;
		}
		const name = `tuple<${Object.entries(exprShape)
			.map(([key, val]) => `${key}: ${val.__element__.__name__}`)
			.join(', ')}>`;
		return $expressionify({
			__kind__: ExpressionKind.NamedTuple,
			__element__: {
				__kind__: TypeKind.namedtuple,
				__name__: name,
				__shape__: typeShape
			},
			__cardinality__: cardutil.multiplyCardinalitiesVariadic(Object.values(exprShape).map((val) => val.__cardinality__)),
			__shape__: exprShape
		});
	}
}
export function $objectTypeToTupleType(...args) {
	const [objExpr, fields] = args;
	const shape = Object.entries(objExpr.__element__.__pointers__).reduce((_shape, [key, val]) => {
		if (fields?.length ? fields.includes(key) : key !== 'id' && val.__kind__ === 'property' && !val.computed) {
			_shape[key] = val.target;
		}
		return _shape;
	}, {});
	return tuple(shape);
}
