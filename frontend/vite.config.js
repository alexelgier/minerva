import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

import { fileURLToPath, URL } from 'url';

export default defineConfig({
	plugins: [vue()],
	root: '.',
	publicDir: 'public',
	resolve: {
		alias: {
			'@': fileURLToPath(new URL('./src', import.meta.url)),
		},
	},
	build: {
		outDir: 'dist',
		emptyOutDir: true,
	},
	server: {
		open: true,
	},
});
