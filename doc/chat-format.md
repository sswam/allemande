Chat file format:

A chat entry has a user and a message, in this format:

User:	message line 1
	message line 2
	...

The user is followed by a colon and a tab. Secondary lines if any are indented with a tab.

The chat file is a sequence of chat entries.

When writing a chat file, we will strictly follow the format. There is an option to use spaces instead of tabs for indentation.

When reading a chat file, we can optionally be strict or lenient, and accept any of the following:

- spaces instead of tabs
- user:message, without spacing
- continuation lines without indentation
- blank continuation lines, without indentation

A play file is a chat file which also allows other narrative text, without a
user prefix. When reading such a file, continuation lines must be indented to
distinguish them from narrative text.

A story file might not have any user prefixes at all.

The parsed form, is similar to Open AI's records for their Chat API:

	message_obj = {"role": role, "content": message}

However we will use the user name and omit the role for the moment.

	message_obj = {"user": user, "content": message}

We will also allow for a timestamp as a future extension.

In the case of narrative text, we will omit the user field.

When converting for sticter 3rd-party AI APIs such as OpenAI or Anthropic, we
will need to add a role field based on the user field, exclude narrative text
or convert it to "system" messages, and perhaps make other changes.

Ideas:

- timestamps?  not yet
	- should we always include timestamps, or allow them to be omitted?
	- if we do include them, how would they be formatted?
	- don't include them for now
	- could be included in a separate column at the left
		- in YYYY-MM-DD HH:MM:SS format
		- maybe with .NNNNNNNNN fraction of second / milliseconds / microseconds / nanosenconds
		- could include the user's timezone
		- could include the weekday in human-readable format
		- putting the timestamp at the left allows for easy sorting
		- but, I don't want to include the timestamp on continuation lines
- separate messages with blank lines
	- this is recommended but not enforced
