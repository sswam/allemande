You're right that mixing `import` statements with conditional logic is problematic - `import` statements are hoisted and will fail in browser environments. Here's a cleaner approach:

```javascript
// ---------- exports / entry ----------

// CommonJS (Node.js)
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
  module.exports = { parse, format };
}

// Browser global
if (typeof window !== 'undefined') {
  window.ym = { parse, format };
}

// ES Module / Deno entry point - put this in a separate block at the bottom
// using dynamic import to avoid hoisting issues
if (typeof process !== 'undefined' && typeof require !== 'undefined') {
  // Node.js CommonJS main check
  if (require.main === module) main();
} else if (typeof Deno !== 'undefined') {
  // Deno main check
  if (import.meta.main) main();
} else if (typeof import.meta !== 'undefined') {
  // Node.js ESM main check - dynamic to avoid parse errors in non-ESM environments
  import('url').then(({ fileURLToPath }) =>
    import('fs').then(({ realpathSync }) => {
      if (realpathSync(fileURLToPath(import.meta.url)) === realpathSync(process.argv[1])) {
        main();
      }
    })
  );
}
```

But honestly, **the cleanest real-world solution** is a separate thin entry point:

```javascript
// cli.js  (or main.js)
import { main } from './yourmodule.js';
main();
```

And keep the library file as pure library code. The "is this the main module" detection is inherently messy across environments - a dedicated entry file sidesteps the whole problem and is the conventional approach.

Key issues with mixing `import` and conditional logic:
- `import` statements are **static** and hoisted before any code runs
- They'll throw in environments where the modules don't exist
- `import.meta` itself can be a **syntax error** in non-ESM contexts

If you truly need a single-file solution, the dynamic `import()` approach above is the safest, but it makes the main-detection async which has its own tradeoffs.
