// GENERATED by @edgedb/generate v0.5.3

import type { $bool, $number } from './modules/std';
import { Cardinality, ExpressionKind } from 'edgedb/dist/reflection/index';
import { cardutil } from './cardinality';
import type {
	$expr_PolyShapeElement,
	$scopify,
	Expression,
	LinkDesc,
	ObjectType,
	ObjectTypeExpression,
	ObjectTypePointers,
	ObjectTypeSet,
	PrimitiveTypeSet,
	PropertyDesc,
	ScalarType,
	stripSet,
	TypeSet,
	BaseType,
	ExclusiveTuple,
	orLiteralValue,
	EnumType
} from './typesystem';
import { type $expr_PathLeaf, type $linkPropify, type ExpressionRoot } from './path';
import type { anonymizeObject } from './casting';
import { type scalarLiterals, type literalToScalarType } from './castMaps';
export declare const ASC: 'ASC';
export declare const DESC: 'DESC';
export declare const EMPTY_FIRST: 'EMPTY FIRST';
export declare const EMPTY_LAST: 'EMPTY LAST';
export type OrderByDirection = 'ASC' | 'DESC';
export type OrderByEmpty = 'EMPTY FIRST' | 'EMPTY LAST';
export type OrderByExpr = TypeSet<ScalarType | EnumType | ObjectType, Cardinality>;
export type OrderByObjExpr = {
	expression: OrderByExpr;
	direction?: OrderByDirection;
	empty?: OrderByEmpty;
};
export type OrderByExpression = OrderByExpr | OrderByObjExpr | [OrderByExpr | OrderByObjExpr, ...(OrderByExpr | OrderByObjExpr)[]];
export type OffsetExpression = TypeSet<$number, Cardinality.Empty | Cardinality.One | Cardinality.AtMostOne>;
export type SelectFilterExpression = TypeSet<$bool, Cardinality>;
export type LimitOffsetExpression = TypeSet<$number, Cardinality.Empty | Cardinality.One | Cardinality.AtMostOne>;
export type LimitExpression = TypeSet<$number, Cardinality.Empty | Cardinality.One | Cardinality.AtMostOne>;
export type SelectModifierNames = 'filter' | 'filter_single' | 'order_by' | 'offset' | 'limit';
type filterSingle<T extends TypeSet> = T extends ObjectTypeSet ? TypeSet<anonymizeObject<T['__element__']>, T['__cardinality__']> : orLiteralValue<T>;
export type exclusivesToFilterSingle<E extends ExclusiveTuple> = ExclusiveTuple extends E
	? never
	: E extends []
		? never
		: {
				[j in keyof E]: {
					[k in keyof E[j]]: filterSingle<E[j][k]>;
				};
			}[number];
export type SelectModifiers<T extends ObjectType = ObjectType> = {
	filter?: SelectFilterExpression;
	filter_single?: exclusivesToFilterSingle<T['__exclusives__']> | SelectFilterExpression;
	order_by?: OrderByExpression;
	offset?: OffsetExpression | number;
	limit?: LimitExpression | number;
};
export type UnknownSelectModifiers = {
	[k in keyof SelectModifiers]: unknown;
};
export type NormalisedSelectModifiers = {
	filter?: SelectFilterExpression;
	order_by?: OrderByObjExpr[];
	offset?: OffsetExpression;
	limit?: LimitExpression;
	singleton: boolean;
};
export type $expr_Select<Set extends TypeSet = TypeSet> = Expression<{
	__element__: Set['__element__'];
	__cardinality__: Set['__cardinality__'];
	__expr__: TypeSet;
	__kind__: ExpressionKind.Select;
	__modifiers__: NormalisedSelectModifiers;
	__scope__?: ObjectTypeExpression;
}>;
export interface SelectModifierMethods<Root extends TypeSet> {
	filter<Filter extends SelectFilterExpression>(
		filter: Filter | ((scope: Root extends ObjectTypeSet ? $scopify<Root['__element__']> : stripSet<Root>) => Filter)
	): this;
	order_by(
		order_by: OrderByExpression | ((scope: Root extends ObjectTypeSet ? $scopify<Root['__element__']> : stripSet<Root>) => OrderByExpression)
	): this;
	offset(
		offset:
			| OffsetExpression
			| number
			| ((scope: Root extends ObjectTypeSet ? $scopify<Root['__element__']> : stripSet<Root>) => OffsetExpression | number)
	): this;
	limit(
		limit:
			| LimitExpression
			| number
			| ((scope: Root extends ObjectTypeSet ? $scopify<Root['__element__']> : stripSet<Root>) => LimitExpression | number)
	): this;
}
export type InferOffsetLimitCardinality<Card extends Cardinality, Modifiers extends UnknownSelectModifiers> = Modifiers['limit'] extends
	| number
	| LimitExpression
	? cardutil.overrideLowerBound<Card, 'Zero'>
	: Modifiers['offset'] extends number | OffsetExpression
		? cardutil.overrideLowerBound<Card, 'Zero'>
		: Card;
export type ComputeSelectCardinality<Expr extends ObjectTypeExpression, Modifiers extends UnknownSelectModifiers> = InferOffsetLimitCardinality<
	undefined extends Modifiers['filter_single'] ? Expr['__cardinality__'] : cardutil.overrideUpperBound<Expr['__cardinality__'], 'One'>,
	Modifiers
>;
export declare function is<
	Expr extends ObjectTypeExpression,
	Shape extends objectTypeToSelectShape<Expr['__element__']>,
	ReturnT extends {
		[k in Exclude<keyof Shape, SelectModifierNames | 'id'>]: $expr_PolyShapeElement<Expr, normaliseElement<Shape[k]>>;
	}
>(expr: Expr, shape: Shape): ReturnT;
export declare function $handleModifiers(
	modifiers: SelectModifiers,
	params: {
		root: TypeSet;
		scope: TypeSet;
	}
): {
	modifiers: NormalisedSelectModifiers;
	cardinality: Cardinality;
	needsAssertSingle: boolean;
};
export type $expr_Delete<Root extends ObjectTypeSet = ObjectTypeSet> = Expression<{
	__kind__: ExpressionKind.Delete;
	__element__: Root['__element__'];
	__cardinality__: Root['__cardinality__'];
	__expr__: ObjectTypeSet;
}>;
declare function deleteExpr<Expr extends ObjectTypeExpression, Modifiers extends SelectModifiers<Expr['__element__']>>(
	expr: Expr,
	modifiers?: (scope: $scopify<Expr['__element__']>) => Readonly<Modifiers>
): $expr_Delete<{
	__element__: ObjectType<
		Expr['__element__']['__name__'],
		Expr['__element__']['__pointers__'],
		{
			id: true;
		}
	>;
	__cardinality__: ComputeSelectCardinality<Expr, Modifiers>;
}>;
export { deleteExpr as delete };
export declare function $selectify<Expr extends ExpressionRoot>(expr: Expr): Expr;
export type linkDescToLinkProps<Desc extends LinkDesc> = {
	[k in keyof Desc['properties'] & string]: $expr_PathLeaf<TypeSet<Desc['properties'][k]['target'], Desc['properties'][k]['cardinality']>>;
};
export type pointersToObjectType<P extends ObjectTypePointers> = ObjectType<string, P, object>;
type linkDescToShape<L extends LinkDesc> = objectTypeToSelectShape<L['target']> &
	objectTypeToSelectShape<pointersToObjectType<L['properties']>> &
	SelectModifiers;
type linkDescToSelectElement<L extends LinkDesc> =
	| boolean
	| TypeSet<anonymizeObject<L['target']>, cardutil.assignable<L['cardinality']>>
	| linkDescToShape<L>
	| ((scope: $scopify<L['target']> & linkDescToLinkProps<L>) => linkDescToShape<L>);
type propDescToSelectElement<P extends PropertyDesc> = boolean | TypeSet<P['target'], cardutil.assignable<P['cardinality']>> | $expr_PolyShapeElement;
export type objectTypeToSelectShape<T extends ObjectType = ObjectType, Pointers extends ObjectTypePointers = T['__pointers__']> = Partial<{
	[k in keyof Pointers]: Pointers[k] extends PropertyDesc
		? propDescToSelectElement<Pointers[k]>
		: Pointers[k] extends LinkDesc
			? linkDescToSelectElement<Pointers[k]>
			: any;
}> & {
	[k: string]: unknown;
};
export type normaliseElement<El> = El extends boolean
	? El
	: El extends TypeSet
		? stripSet<El>
		: El extends (...scope: any[]) => any
			? normaliseShape<ReturnType<El>>
			: El extends object
				? normaliseShape<stripSet<El>>
				: stripSet<El>;
export type normaliseShape<Shape extends object, Strip = SelectModifierNames> = {
	[k in Exclude<keyof Shape, Strip>]: normaliseElement<Shape[k]>;
};
export declare const $existingScopes: Set<Expression<TypeSet<BaseType, Cardinality>>>;
declare function $shape<
	Expr extends ObjectTypeExpression,
	Element extends Expr['__element__'],
	Shape extends objectTypeToSelectShape<Element> & SelectModifiers<Element>,
	SelectCard extends ComputeSelectCardinality<Expr, Modifiers>,
	SelectShape extends normaliseShape<Shape, SelectModifierNames>,
	Scope extends $scopify<Element> &
		$linkPropify<{
			[k in keyof Expr]: k extends '__cardinality__' ? Cardinality.One : Expr[k];
		}>,
	Modifiers extends UnknownSelectModifiers = Pick<Shape, SelectModifierNames>
>(
	expr: Expr,
	_shape: (scope: Scope) => Readonly<Shape>
): ((scope: unknown) => Readonly<Shape>) & TypeSet<ObjectType<Element['__name__'], Element['__pointers__'], SelectShape>, SelectCard>;
export { $shape as shape };
export declare function select<
	Expr extends ObjectTypeExpression,
	Element extends Expr['__element__'],
	ElementName extends `${Element['__name__']}`,
	ElementPointers extends Element['__pointers__'],
	ElementShape extends Element['__shape__'],
	Card extends Expr['__cardinality__']
>(
	expr: Expr
): $expr_Select<{
	__element__: ObjectType<ElementName, ElementPointers, ElementShape>;
	__cardinality__: Card;
}>;
export declare function select<Expr extends TypeSet>(expr: Expr): $expr_Select<stripSet<Expr>>;
export declare function select<
	Expr extends ObjectTypeExpression,
	Element extends Expr['__element__'],
	Shape extends objectTypeToSelectShape<Element> & SelectModifiers<Element>,
	SelectCard extends ComputeSelectCardinality<Expr, Modifiers>,
	SelectShape extends normaliseShape<Shape, SelectModifierNames>,
	Scope extends $scopify<Element> &
		$linkPropify<{
			[k in keyof Expr]: k extends '__cardinality__' ? Cardinality.One : Expr[k];
		}>,
	ElementName extends `${Element['__name__']}`,
	Modifiers extends UnknownSelectModifiers = Pick<Shape, SelectModifierNames>
>(
	expr: Expr,
	shape: (scope: Scope) => Readonly<Shape>
): $expr_Select<{
	__element__: ObjectType<ElementName, Element['__pointers__'], SelectShape>;
	__cardinality__: SelectCard;
}>;
export declare function select<Expr extends PrimitiveTypeSet, Modifiers extends SelectModifiers>(
	expr: Expr,
	modifiers: (expr: Expr) => Readonly<Modifiers>
): $expr_Select<{
	__element__: Expr['__element__'];
	__cardinality__: InferOffsetLimitCardinality<Expr['__cardinality__'], Modifiers>;
}>;
export declare function select<
	Shape extends {
		[key: string]: TypeSet;
	}
>(
	shape: Shape
): $expr_Select<{
	__element__: ObjectType<
		`std::FreeObject`,
		{
			[k in keyof Shape]: Shape[k]['__element__'] extends ObjectType
				? LinkDesc<Shape[k]['__element__'], Shape[k]['__cardinality__'], {}, false, true, true, false>
				: PropertyDesc<Shape[k]['__element__'], Shape[k]['__cardinality__'], false, true, true, false>;
		},
		Shape
	>;
	__cardinality__: Cardinality.One;
}>;
export declare function select<Expr extends scalarLiterals>(
	expr: Expr
): $expr_Select<{
	__element__: literalToScalarType<Expr>;
	__cardinality__: Cardinality.One;
}>;
export declare function resolveShapeElement(key: any, value: any, scope: ObjectTypeExpression): any;
