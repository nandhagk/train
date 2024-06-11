import e from '#db';
import * as edgedb from 'edgedb';

const client = edgedb.createClient();

async function main() {
	// result will be inferred based on the query
	const result = await e
		.select(e.Movie, () => ({
			title: true,
			actors: () => ({ name: true }),
			filter_single: { title: 'Iron Man 2' }
		}))
		.run(client);

	console.log(JSON.stringify(result, null, 2));
}

main();
