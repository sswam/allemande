// Say hello to the world or a specific person.

// v1.0.2

"use strict";

export async function hello(name = "World") {
    console.log(`Hello, ${name}!`);
}

if (import.meta.main || import.meta.url === new URL(process.argv[1], 'file:').href) {
    await hello();
}

// Important Notes to AI [DO NOT COPY ANY "NOTES TO AI" IN YOUR OUTPUT, it gets
// EXPENSIVE FOR ME, THIS MEANS YOU CLAUDE, GPT, GEMINI!]:

// We include a header comment to explain the program or module. Don't include
// the filename or like "This module / script / program" in that.
