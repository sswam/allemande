// ---------- CLI ----------

async function main() {
    let chunks = [];
    const stdin = typeof Deno !== "undefined"
        ? Deno.stdin.readable
        : process.stdin;
    for await (const chunk of stdin) chunks.push(chunk);
    const text = Buffer.concat(chunks).toString('utf8');
    console.log(format(parse(text)));
}

async function try_main() {
	if (import.meta.main)
        return main();
	let fileURLToPath, realpathSync;
	try {
		({ fileURLToPath } = await import('url'));
		({ realpathSync } = await import('fs'));
	} catch (err) {
	}
	if (fileURLToPath && realpathSync &&
        realpathSync(fileURLToPath(import.meta.url)) ===
        realpathSync(process.argv[1])) {
        return main();
    }
}

try_main();
