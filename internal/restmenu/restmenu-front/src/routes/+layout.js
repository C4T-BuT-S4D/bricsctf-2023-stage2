/** @type {import('./$types').PageLoad} */
import { PUBLIC_BASE_URL } from '$env/static/public';
export const ssr = false;

export async function load({ fetch }) {
	const res = await fetch(`${PUBLIC_BASE_URL}/api/user`, {
		credentials: 'include'
	});
	let user = null;
	try {
		user = await res.json();
	}
	catch (err) {
		user = null;
	}

	return { user: user };
}