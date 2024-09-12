I want to make the ultimate programming toolkit for writing AI tools, including accessing LLMs both locally and via APIs. An issue with local LLMs is that they take time to load, so I think we need a client-server approach. The server should be able to load and unload models transparently on demand, and not limited to LLMs, also other AI models including Stable Diffusion, whisper, etc. I want the client-server system to use files rather than sockets by default, which is unusual. I.e. I will assemble a request file (as JSON or YAML maybe) along with any attachments it needs in a folder, then move that folder into the server's "inbox" (for me). When the server is done, it will move the folder including results into its outbox for me, where my program will notice it. I'll using inotfy or similar so that this is responsive. What do you think of the idea? Can avoid the need for complex attachment encodings. For remote requests we can either use an efficient filesystem mount (sshfs seems a bit lacking) or accepted encoded requests over https.

Your proposed client-server approach for AI tools is innovative and has several advantages:

1. Efficient model loading/unloading
2. Support for various AI models
3. File-based communication simplifies attachment handling
4. Asynchronous processing with inotify for responsiveness
5. Flexibility for local and remote requests

Potential challenges:
1. Ensuring file system security
2. Managing concurrent requests
3. Handling large files efficiently

Overall, it's a solid concept that could streamline AI tool development and usage. Consider implementing a prototype to validate the approach and identify any unforeseen issues.
