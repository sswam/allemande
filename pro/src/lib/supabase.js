import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_PUBLIC_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export async function getAccessToken() {
	const { data } = await supabase.auth.getSession();

	if (data && data.session.access_token) {
		return data.session.access_token;
	} else {
		return null;
	}
}
