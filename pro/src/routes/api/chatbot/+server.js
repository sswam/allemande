import { Configuration, OpenAIApi } from 'openai';
import { OPENAI_API_KEY } from '$env/static/private';
import { json } from '@sveltejs/kit';

const configuration = new Configuration({
	apiKey: OPENAI_API_KEY
});

const openai = new OpenAIApi(configuration);

/** @type {import('@sveltejs/kit').RequestHandler} */
export async function POST({ request }) {
	if (!configuration.apiKey) {
		return json(
			{
				error: {
					message: 'OpenAI API key not configured, please follow instructions in README.md'
				}
			},
			500
		);
	}

	const { message, model } = await request.json();
	if (message.trim().length === 0) {
		return json(
			{
				error: {
					message: 'Please enter a message'
				}
			},
			400
		);
	}

	try {
		console.log(`Sending message to OpenAI: ${message}`);
		const completion = await openai.createChatCompletion({
			model: model,
			messages: [{ role: 'user', content: message }]
		});
		const botMessage = completion.data.choices[0].message.content.trim();
		return json({ message: botMessage });
	} catch (error) {
		if (error.response) {
			console.error(error.response.status, error.response.data);
			return json(error.response.data, error.response.status);
		} else {
			console.error(`Error with OpenAI API request: ${error.message}`);
			return json(
				{
					error: {
						message: 'An error occurred during your request.'
					}
				},
				500
			);
		}
	}
}
