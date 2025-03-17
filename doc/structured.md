I don't like JSON output for various reasons\*, so I use this approach:

1. Ask for markdown output, and give an example template
2. Number the headings. This makes it much less likely that the AI will miss sections.
3. Parse the markdown output into sections. If that's difficult for you, ask the AI to show you how. I would tend to use regexps with the multi-line option. I can give parsing examples in Python or JavaScript if that's useful.

That's all!  I haven't seen other people doing this, so I thought I'd share it.

\*Why I don't like JSON output:

* It's much less human readable.
* It's more likely the AI will make a syntax error (not every LLM has JSON mode).
* It requires character escaping in many cases, especially when producing code, text with quotes, or multi-line sections.
* The LLM is less familiar with JSON than with text in Markdown, and following the format might distract it from writing high-quality content.
* If the LLM breaks the JSON format it's not easy to automatically fix it.

JSON output might be better when the actual task is to produce a JSON object, or for deeply nested data structures. I'd also consider using YAML.

Another idea, instead of using CSV for input or output, which is difficult for LLMs, use key: value records and include a row number, like this. This is also good for lists of records where you might otherwise use JSON.

```
i: 0
name: Sam
age: 48

i: 1
name: Frodo
age: 50
```
