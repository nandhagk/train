// GENERATED by @edgedb/generate v0.5.3

import { ExpressionKind, Cardinality } from 'edgedb/dist/reflection/index';
import type { Expression, BaseType, TypeSet, ObjectTypeExpression, ScalarType } from './typesystem';
import type { orScalarLiteral } from './castMaps';
export declare function cast<Target extends BaseType | ObjectTypeExpression>(
	target: Target,
	arg: null
): $expr_Cast<Target extends BaseType ? Target : Target extends ObjectTypeExpression ? Target['__element__'] : never, Cardinality.Empty>;
export declare function cast<Target extends ObjectTypeExpression, Card extends Cardinality>(
	target: Target,
	arg: TypeSet<ScalarType<'std::uuid'>, Card>
): $expr_Cast<Target['__element__'], Card>;
export declare function cast<Target extends BaseType, Expr extends TypeSet>(
	target: Target,
	expr: orScalarLiteral<Expr>
): $expr_Cast<Target, Cardinality extends Expr['__cardinality__'] ? Cardinality.One : Expr['__cardinality__']>;
export type $expr_Cast<Target extends BaseType = BaseType, Card extends Cardinality = Cardinality> = Expression<{
	__element__: Target;
	__cardinality__: Card;
	__kind__: ExpressionKind.Cast;
	__expr__: TypeSet | null;
}>;
