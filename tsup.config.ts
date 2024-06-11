import { defineConfig } from 'tsup';

export default defineConfig({
	dts: false,
	clean: true,
	shims: false,
	entry: ['src/**/*.ts', '!src/**/*.d.ts'],
	minify: false,
	bundle: false,
	target: 'esnext',
	format: ['esm'],
	tsconfig: 'src/tsconfig.json',
	sourcemap: true,
	keepNames: true,
	splitting: false,
	skipNodeModulesBundle: true
});
