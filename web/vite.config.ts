import { defineConfig } from "vite";
export default defineConfig({
  base: "./",
  build: {
    outDir: "../app/src/main/assets/dashboard",
    emptyOutDir: true,
    target: "es2020",
  },
  server: { host: "127.0.0.1", port: 4173, strictPort: true },
});
