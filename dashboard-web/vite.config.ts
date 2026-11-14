import { defineConfig } from "vite";
// En desarrollo /api se reenvía al backend administrativo, que solo escucha en loopback.
// Configura origin "http://127.0.0.1:4174" en private/dashboard-admin.local.json mientras uses `npm run dev`.
export default defineConfig({
  base: "./",
  build: { outDir: "dist", emptyOutDir: true, target: "es2020" },
  server: {
    host: "127.0.0.1",
    port: 4174,
    strictPort: true,
    proxy: { "/api": "http://127.0.0.1:8787" },
  },
});
