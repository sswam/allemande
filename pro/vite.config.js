import { sveltekit } from '@sveltejs/kit/vite';

/** @type {import('vite').UserConfig} */
const config = {
	plugins: [sveltekit()],
	server: {
		// use same port as prod server for dev server, for compatibility
		port: 3000,  // 5173,
		strictPort: false,
	},
	preview: {
		port: 4173,
		strictPort: false,
	}
};

export default config;
