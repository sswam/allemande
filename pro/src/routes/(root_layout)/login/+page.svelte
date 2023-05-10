<script>
	import { supabase } from '$lib/supabase';
	import { goto } from '$app/navigation';

	let email = '';
	let password = '';
	let errors = {};
	let isLoading = false;
	let error = '';

	function handleSubmit() {
		validateForm();

		if (Object.keys(errors).length === 0) {
			signIn();
		}
	}

	async function signIn() {
		isLoading = true;

		const { error: signInError } = await supabase.auth.signInWithPassword({
			email,
			password
		});

		if (signInError) {
			error = signInError.message;
		} else {
			goto('/chatbot');
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
	<label for="email">
		Email:
		<input type="email" id="email" bind:value={email} class:error={errors.email} />
		{#if errors.email}
			<p class="error">{errors.email}</p>
		{/if}
	</label>
	<label for="password">
		Password:
		<input type="password" id="password" bind:value={password} class:error={errors.password} />
		{#if errors.password}
			<p class="error">{errors.password}</p>
		{/if}
	</label>
	<div class="form-links">
		<a href="/signup">Create an account</a>
		<a href="/password-reset">Forgotten password?</a>
	</div>
	<button type="submit" disabled={isLoading}>
		{#if isLoading}
			Loading...
		{:else}
			Log in
		{/if}
		{#if isLoading}
			<span class="loading-spinner" />
		{/if}
	</button>

	{#if error}
		<p class="error">{error}</p>
	{/if}
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
	}

	input {
		padding: 0.5rem;
		font-size: 1rem;
		border: 2px solid #ccc;
		border-radius: 5px;
		width: 100%;
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
	}

	button[type='submit']:hover {
		background-color: #0055a7;
	}

	button[type='submit']:disabled {
		opacity: 0.7;
		cursor: not-allowed;
	}

	.form-links {
		display: flex;
		justify-content: space-between;
		width: 100%;
		margin-top: 1rem;
	}

	.form-links a {
		color: #007aff;
		text-decoration: none;
		font-size: 0.8rem;
		display: inline-block;
		text-align: center;
	}

	.form-links a:hover {
		text-decoration: underline;
	}

	.form-links {
		margin-top: 0.01rem;
	}

	.loading-spinner {
		display: inline-block;
		margin-left: 0.5rem;
		border: 3px solid rgba(0, 0, 0, 0.1);
		border-top-color: #007aff;
		border-radius: 50%;
		width: 0.8rem;
		height: 0.8rem;
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
