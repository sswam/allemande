<script>
	import { supabase } from '$lib/supabase';
	import { goto } from '$app/navigation';

	let email = '';
	let password = '';
	let errors = {};
	let isLoading = false;

	function handleSubmit() {
		validateForm();

		if (Object.keys(errors).length === 0) {
			signUp();
		}
	}

	async function signUp() {
		isLoading = true;

		const { data, error: signUpError } = await supabase.auth.signUp({
			email,
			password
		});

		if (signUpError) {
			error = signUpError.message;
		} else {
			goto('/login');
		}

		isLoading = false;
	}

	function validateForm() {
		errors = {};

		if (!email) {
			errors.email = 'Email is required';
		} else if (!/\S+@\S+\.\S+/.test(email)) {
			errors.email = 'Email is invalid';
		}

		if (!password) {
			errors.password = 'Password is required';
		}

		return errors;
	}
</script>

<form on:submit|preventDefault={handleSubmit}>
	<label>
		Email:
		<input type="email" bind:value={email} class:error={errors.email} />
		{#if errors.email}
			<p class="error">{errors.email}</p>
		{/if}
	</label>
	<label>
		Password:
		<input type="password" bind:value={password} class:error={errors.password} />
		{#if errors.password}
			<p class="error">{errors.password}</p>
		{/if}
	</label>

	<button type="submit" disabled={Object.keys(errors).length > 0}>
		{#if Object.keys(errors).length > 0}
			<span class="error">Please fix errors before submitting</span>
		{:else}
			Sign up
		{/if}
		{#if isLoading}
			<span class="loading-spinner" />
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

	.error {
		margin-top: 0.5rem;
		color: red;
		font-size: 0.8rem;
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
