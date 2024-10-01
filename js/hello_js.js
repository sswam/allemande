// v1.0.1

"use strict";

export async function hello(name = "World") {
   try {
      console.log(`Hello, ${name}!`);
   } catch (error) {
      handleError(error);
   }
}

function handleError(error) {
   console.error(`An error occurred: ${error.message}`);
}

// Check if the module is being run directly
if (typeof window === "undefined" && import.meta.url === `file://${process.argv[1]}`) {
   await hello();
}

// Important Notes for AI:
// - perfer for (const varname of list) { ... } over list.forEach
// - always use async / await not promises with .then and .catch and not callbacks
// - don't use IIFEs, use ECMAScript modules
// - don't use ==, use ===
// - use regular functions, not arrow functions
// - prefer double quotes over single quotes
// - use `template ${var} literals`
// - always 'use strict'
// - centralize error handling
// - write code than runs in the browser, node, and Deno
// When writing other scripts based on this one, please do not include these notes!
