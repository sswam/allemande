<script>
	let messageInput = '';
	let messages = [];
	let model = 'gpt-3.5-turbo';
	let isTyping = false;

	const sendMessage = async (message) => {
		messages = [...messages, { text: message, isUser: true }];
		isTyping = true;
		try {
			const response = await fetch('/api/chatbot', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ message, model })
			});

			if (!response.ok) {
				throw new Error(`Request failed with status ${response.status}`);
			}

			if (response.headers.get('Content-Type') !== 'application/json') {
				throw new Error('Unexpected content type in server response');
			}

			const data = await response.json();

			messages = [...messages, { text: data.message, isUser: false }];
		} catch (error) {
			console.error(error);
			messages = [...messages, { text: error.message, isUser: false }];
		} finally {
			isTyping = false;
		}
	};

	const onSubmit = async (event) => {
		event.preventDefault();
		const message = messageInput.trim();
		if (message.length === 0) return;
		messageInput = '';
		await sendMessage(message);
	};
</script>

<h1>Chatbot</h1>
<div class="model-selection">
	<label for="model">Model:</label>
	<select id="model" bind:value={model}>
		<option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
		<option value="gpt-4">gpt-4</option>
	</select>
</div>

<div class="messages">
	{#each messages as message}
		<div class={message.isUser ? 'userMessage' : 'botMessage'}>
			{message.text}
		</div>
	{/each}
	{#if isTyping}
		<div class="botMessage">
			<div class="typing-dots">
				<div />
				<div />
				<div />
			</div>
		</div>
	{/if}
</div>
<form on:submit={onSubmit}>
	<input
		type="text"
		name="message"
		placeholder="Type your message here"
		bind:value={messageInput}
	/>
	<button type="submit">Send</button>
</form>

<style>
	h1 {
		text-align: center;
		margin-bottom: 20px;
		font-size: 2rem;
	}

	/* Add a media query for smaller screens */
	@media (max-width: 560px) {
		h1 {
			text-align: left;
			margin-left: 20px;
		}
	}

	.messages {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.userMessage {
		max-width: 60%;
		padding: 10px;
		border-radius: 10px;
		background-color: #ddd;
		align-self: flex-start;
	}

	.botMessage {
		max-width: 60%;
		padding: 10px;
		border-radius: 10px;
		background-color: #eee;
		align-self: flex-end;
	}

	form {
		display: flex;
		gap: 10px;
		margin-top: 20px;
		margin-bottom: 60px;
	}

	input[type='text'] {
		flex: 1;
		padding: 10px;
		border-radius: 10px;
		border: none;
		outline: none;
		background-color: #eee;
	}

	button[type='submit'] {
		padding: 10px 20px;
		border-radius: 10px;
		border: none;
		outline: none;
		background-color: #0070f3;
		color: #fff;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.2s;
	}

	button[type='submit']:hover {
		background-color: #006ae6;
	}

	.model-selection {
		position: absolute;
		top: 10px;
		right: 10px;
	}

	.typing-dots {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.typing-dots div {
		width: 6px;
		height: 6px;
		background-color: #333;
		border-radius: 50%;
		margin: 0 2px;
		animation: typing-dots 1.4s infinite ease-in-out;
	}

	.typing-dots div:nth-child(2) {
		animation-delay: 0.2s;
	}

	.typing-dots div:nth-child(3) {
		animation-delay: 0.4s;
	}

	@keyframes typing-dots {
		0%,
		80%,
		100% {
			transform: translateY(0);
		}
		40% {
			transform: translateY(-6px);
		}
	}
</style>
