import { supabase } from '$lib/supabase';
import { redirect } from '@sveltejs/kit';

/** @type {import('./$types').PageLoad} */
export const load = async () => {
	const {
		data: { session }
	} = await supabase.auth.getSession();
	let user = session?.user;

	if (!user) {
		throw redirect(302, '/login');
	}
};
