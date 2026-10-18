import { resolve } from "node:path";
import { defineConfig } from "vitest/config";

// Dev server proxies the API to uvicorn on :8000 (`make server`).
// 127.0.0.1, not localhost: Node may resolve localhost to ::1 while uvicorn listens on IPv4.
const API = "http://127.0.0.1:8000";

export default defineConfig({
  server: {
    port: 5173,
    strictPort: true,
    host: true, // reachable from phones on the same LAN, and from cloudflared
    allowedHosts: [".trycloudflare.com"], // `make tunnel` hostnames
    proxy: {
      "/api": { target: API, changeOrigin: true },
      "/ws": { target: API.replace("http", "ws"), ws: true, changeOrigin: true },
    },
  },
  build: {
    rollupOptions: {
      input: {
        capture: resolve(import.meta.dirname, "index.html"),
        record: resolve(import.meta.dirname, "record.html"),
        console: resolve(import.meta.dirname, "console.html"),
      },
    },
  },
  test: {
    include: ["tests/unit/**/*.test.ts"],
    environment: "node",
  },
});
