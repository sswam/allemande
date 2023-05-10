<script>
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/supabase';

	let password = '';
	let isLoading = false;
	let error = '';

	async function handleSubmit() {
		isLoading = true;
		const { data, error: updateError } = await supabase.auth.updateUser({ password: password });

		if (updateError) {
			error = updateError.message;
			isLoading = false;
		} else {
			alert('Password updated!');
			await supabase.auth.signOut();
			goto('/login');
			isLoading = false;
		}
	}
</script>

<form on:submit|preventDefault={handleSubmit}>
	<label>
		New Password:
		<input type="password" bind:value={password} class:error />
		{#if error}
			<p class="error">{error}</p>
		{/if}
	</label>
	<button type="submit" disabled={isLoading}>
		{#if isLoading}
			<span class="loading-spinner" />
			Loading...
		{:else}
			Update Password
		{/if}
	</button>
</form>

<style>
	form {
		display: flex;
		flex-direction: column;
		align-items: center;
		margin: 0 auto;
		max-width: 400px;
	}

	label {
		display: flex;
		flex-direction: column;
		margin-bottom: 1rem;
		width: 100%;
		color: #333;
	}

	input {
		padding: 0.5rem;
		font-size: 1rem;
		border: 2px solid #ccc;
		border-radius: 5px;
		width: 100%;
		color: #333;
	}

	input.error {
		border-color: red;
	}

	.error {
		color: red;
		margin-top: 0.5rem;
		font-size: 0.8rem;
	}

	button[type='submit'] {
		padding: 0.5rem;
		background-color: #007aff;
		color: white;
		border: none;
		border-radius: 5px;
		font-size: 1rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}

	button[type='submit']:hover {
		background-color: #0055a7;
	}

	button[type='submit'] span.loading-spinner {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		border: 2px solid rgba(0, 0, 0, 0.1);
		border-top-color: #007aff;
		border-radius: 50%;
		width: 1rem;
		height: 1rem;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	label:focus-within {
		color: #007aff;
	}

	input:focus {
		border-color: #007aff;
	}
</style>
