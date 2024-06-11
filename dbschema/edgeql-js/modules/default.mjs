// GENERATED by @edgedb/generate v0.5.3

import * as $ from '../reflection.mjs';
import * as _ from '../imports.mjs';
const $Movie = $.makeType(_.spec, 'e6f69320-27f7-11ef-9bc3-0714f6272d26', _.syntax.literal);

const Movie = _.syntax.$PathNode($.$toSet($Movie, $.Cardinality.Many), null);

const $Person = $.makeType(_.spec, 'e6f56dd4-27f7-11ef-9169-e9711e8ed8c8', _.syntax.literal);

const Person = _.syntax.$PathNode($.$toSet($Person, $.Cardinality.Many), null);

export { $Movie, Movie, $Person, Person };

const __defaultExports = {
	Movie: Movie,
	Person: Person
};
export default __defaultExports;
