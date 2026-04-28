async function try_main() {
    if (typeof require !== 'undefined' && require.main === module)
        return main();
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

if (typeof module !== 'undefined') module.exports = { parse, format };
if (typeof window !== 'undefined') window.ym = { parse, format };
if (typeof require !== 'undefined' && require.main === module) main();
try_main();
