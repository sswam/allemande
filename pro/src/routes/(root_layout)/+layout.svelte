<script>
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/supabase';

	let user;

	supabase.auth.onAuthStateChange((_, session) => {
		user = session?.user;
	});

	async function handleSignOut() {
		const { error } = await supabase.auth.signOut();
		if (error) {
			console.error(error);
		} else {
			goto('/');
		}
	}
</script>

<slot />

<div id="footer" />

<div id="user-info">
	{#if user}
		<span id="user-email">{user.email}</span>
		<button on:click={handleSignOut}>Sign Out</button>
	{/if}
</div>

<style>
	#user-info {
		position: fixed;
		bottom: 20px;
		right: 20px;
		display: flex;
		align-items: center;
		z-index: 1;
	}
	#user-email {
		margin-right: 10px;
	}
	#footer {
		position: fixed;
		bottom: 0;
		left: 0;
		width: 100%;
		height: 60px;
		background-color: white;
		z-index: 0;
	}
</style>
