import { defineConfig } from 'vitest/config'
import preact from '@preact/preset-vite'
import { readFileSync } from 'node:fs'

const version = (JSON.parse(readFileSync(new URL('./package.json', import.meta.url), 'utf8')) as { version: string }).version

export default defineConfig({
  plugins: [preact()],
  base: './',
  define: { __APP_VERSION__: JSON.stringify(version) },
  build: { outDir: 'www', emptyOutDir: true, target: 'es2020' },
  test: { environment: 'jsdom', include: ['src/**/*.test.ts', 'src/**/*.test.tsx'] },
})
