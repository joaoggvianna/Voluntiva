import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Tailwind v4 é plugin do Vite: não existe mais tailwind.config.js nem
// postcss.config.js — o tema fica em src/index.css, no bloco @theme.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  return {
    plugins: [react(), tailwindcss()],
    // O alias "@" precisa existir aqui também: os paths do tsconfig valem
    // só para o type-check, não para a resolução no bundle.
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    server: {
      port: 5173,
      host: true, // necessário para funcionar dentro do container
      proxy: {
        // Evita CORS em desenvolvimento: o navegador fala só com :5173.
        '/api': { target: env.VITE_API_URL ?? 'http://localhost:8000', changeOrigin: true },
        '/ws': { target: env.VITE_WS_URL ?? 'ws://localhost:8000', ws: true },
      },
    },
    build: { outDir: 'dist', sourcemap: mode !== 'production' },
  }
})
