Here's a compact API summary for Hyphenopoly in markdown:

```markdown
# Hyphenopoly API

## Browser Usage

### Configuration

```js
Hyphenopoly.config({
  require: {
    "lang1": "longword1",
    "lang2": "longword2"
  },
  setup: {
    selectors: {
      ".hyphenate": {}
    }
  }
});
```

- `require`: Object with language codes and sample words
- `setup.selectors`: Object with CSS selectors to hyphenate

### CSS

Enable hyphenation:

```css
.hyphenate {
  hyphens: auto;
}
```

## Node.js Usage

```js
import hyphenopoly from "hyphenopoly";

const hyphenator = hyphenopoly.config({
  require: ["lang1", "lang2"],
  hyphen: "•",
  exceptions: {
    "lang": "ex-cep-tion" 
  },
  loader: async (file, dir) => {
    // Custom loader function
  }
});

const hyphenate = await hyphenator.get("lang");
hyphenate("text to hyphenate");
```

- `config()`: Configure hyphenator
- `get()`: Get language-specific hyphenation function
```

This summary covers the key APIs and configuration options for both browser and Node.js usage of Hyphenopoly. Let me know if you need any clarification or additional details!

