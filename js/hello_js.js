// Says hello to the world or a specific person.

// v1.0.2

"use strict";

export async function hello(name = "World") {
    console.log(`Hello, ${name}!`);
}

if (import.meta.main || import.meta.url === new URL(process.argv[1], 'file:').href) {
    await hello();
}
