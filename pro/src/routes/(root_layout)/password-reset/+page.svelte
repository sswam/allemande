<script>
	import { supabase } from '$lib/supabase';

	let email = '';
	let isLoading = false;
	let error = '';

	async function handleSubmit() {
		isLoading = true;
		const { data, error: resetError } = await supabase.auth.resetPasswordForEmail(email);

		if (resetError) {
			error = resetError.message;
			isLoading = false;
		} else {
			alert('Check your email for the password reset link');
			console.log(data);
			isLoading = false;
		}
	}
</script>

<form on:submit|preventDefault={handleSubmit}>
	<label>
		Email:
		<input type="email" bind:value={email} class:error />
		{#if error}
			<p class="error">{error}</p>
		{/if}
	</label>
	<button type="submit" disabled={isLoading}>
		{#if isLoading}
			<span class="loading-spinner" />
			Loading...
		{:else}
			Reset Password
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
