Here's a compact summary of the compromise API in markdown, including key details for expert programmers:

```markdown
# compromise API

## Core Methods

- `nlp(text)` - Parse text and return a Document
- `.match(pattern)` - Find matches in the document
- `.not(pattern)` - Exclude matches  
- `.if(pattern)` - Filter to matches
- `.found` - Boolean if matches exist
- `.text()` - Get text content
- `.json()` - Get structured data
- `.debug()` - Log debug info

## Text Manipulation  

- `.tag(tag)` - Add tags
- `.unTag(tag)` - Remove tags
- `.replace(match, replacement)` - Replace text
- `.remove()` - Remove matches
- `.pre(str)` - Prepend text
- `.post(str)` - Append text
- `.toLowerCase()` - Convert to lowercase
- `.toUpperCase()` - Convert to uppercase

## Iteration

- `.forEach(fn)` - Iterate over matches
- `.map(fn)` - Transform matches
- `.filter(fn)` - Filter matches

## Document Subsets

- `.sentences()` - Get sentences
- `.terms()` - Get individual terms
- `.nouns()`, `.verbs()`, `.adjectives()` etc - Get parts of speech

## Plugins

- `nlp.extend(plugin)` - Add custom functionality

## Key Concepts

- Uses a match syntax for queries
- Returns a chainable Document object
- Provides methods for common NLP tasks
- Extendable with plugins
```

This covers the core functionality an expert programmer would need to use compromise effectively. Let me know if you need any clarification or additional details!

