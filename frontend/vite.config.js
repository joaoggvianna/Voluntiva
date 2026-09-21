import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// O alias "@" precisa existir aqui: os paths do jsconfig/tsconfig valem
// só para o editor e para o type-check, não para a resolução no bundle.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  return {
    plugins: [react()],
    resolve: {
      alias: { '@': path.resolve(__dirname, './src') },
    },
    server: {
      port: 5173,
      host: true, // necessário para funcionar dentro do container
      proxy: {
        // Evita CORS em desenvolvimento: o navegador fala só com :5173.
        // Hoje nenhuma tela usa estas rotas — a UI roda sobre o mock de
        // src/lib/servico.js. O proxy já fica pronto para quando as
        // páginas passarem a chamar src/lib/api.ts.
        '/api': { target: env.VITE_API_URL ?? 'http://localhost:8000', changeOrigin: true },
        '/ws': { target: env.VITE_WS_URL ?? 'ws://localhost:8000', ws: true },
      },
    },
    build: { outDir: 'dist', sourcemap: mode !== 'production' },
  }
})
