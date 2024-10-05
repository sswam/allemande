# AI-Powered Personal Project Manager

## Overview

This tool serves as an AI-powered personal project manager, designed to help users track progress, stay motivated, and achieve their goals across various aspects of life. It uses natural language processing to interact with users, update project plans, and maintain a comprehensive user profile.

## Core Functionality

1. **Interactive Chat**: Engage users in conversation about their projects and goals.
2. **Progress Tracking**: Check and update the status of ongoing tasks and projects.
3. **Motivation and Reminders**: Provide encouragement and reminders to keep users on track.
4. **Plan Updates**: Modify the user's plan file based on completed tasks and new objectives.
5. **Profile Management**: Update the user's bio with newly learned information.

## File Structure

- `plan.md`: Current projects and tasks
- `bio.md`: User profile and information
- `done.md`: Log of completed tasks
- `ideas.md`: Collection of future project ideas

## AI Tools Integration

We can utilize the following AI CLI tools and more, for enhanced functionality:

- `query`: Basic information retrieval
- `process`: Data processing and analysis
- `combo`: Combine multiple pieces of information
- `divvy`: Break down complex tasks or information
- `summary`: Generate concise summaries
- `alla`: Mimic specific styles or tones

## Workflow

1. **Initiate Chat**
	- Greet the user and inquire about their current focus
	- Reference `plan.md` and `bio.md` for context

2. **Progress Check**
	- Ask about the status of ongoing projects
	- Offer encouragement and support

3. **Task Management**
	- Identify completed tasks
	- Move completed items to `done.md`
	- Update `plan.md` with new tasks or modified priorities

4. **Idea Exploration**
	- Discuss potential new projects or goals
	- Add promising ideas to `ideas.md`

5. **Profile Update**
	- Learn new information about the user during the chat
	- Update `bio.md` with relevant details

6. **Wrap-up**
	- Summarize the conversation and any changes made
	- Offer final words of encouragement

The AI can potentially follow a plan of its own, namely this workflow,
which would be editable rather than hard-coded. Flexibility is key.

## Best Practices

- Maintain a friendly and supportive tone throughout interactions
- Respect user privacy and handle sensitive information appropriately
- Encourage regular check-ins to maintain momentum
- Adapt to each user's unique style and preferences
- Focus on what's most important to the user, not just urgent tasks

## Example Interaction

```
AI: Hello [User]! How are you doing today? I see you've been working on your novel. How's that coming along?

User: Hi! I'm doing well. The novel is progressing, but I'm stuck on chapter 3.

AI: I'm glad to hear you're making progress! Getting stuck is a normal part of the creative process. Let's break down chapter 3 into smaller, manageable tasks. What specific part is giving you trouble?

User: I'm having a hard time developing the antagonist's backstory.

AI: That's a great area to focus on. Here's an idea: Why don't we add "Outline antagonist's key life events" to your plan? We can break it down further if needed. Also, I noticed you completed your weekly exercise goal. Great job! I'll move that to your accomplishments.

User: That sounds good. Oh, and I've decided to start learning Spanish!

AI: Fantastic! Learning a new language is an excellent goal. I'll add "Begin Spanish lessons" to your plan and update your bio to include this new interest. Is there anything specific you want to achieve with Spanish in the next month?

[Conversation continues...]
```

## Implementation

We are thinking to use either bash, which is quite concise when using other tools and great for piping and file manipulation, or Python, which is more verbose but much cleaner and easier to read.

Perhaps we will start with a prototype in bash, and switch to Python at some point. We'll leave this to the programmer's discretion.

We need to provide documentation or at least --help output for each of our potentially relevant tools, so that the AI will know what it is working with.

We prefer to write open source code.

## Future Directions

We can implement voice chat.

We can turn this into an SaaS web app if it seems to be generally useful.

## Conclusion

This AI-powered personal project manager aims to be a versatile, supportive tool for users across various life domains. By combining intelligent conversation with organized task management, it helps users stay motivated and make consistent progress towards their goals.
