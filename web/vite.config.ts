import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// scripts/dev.py sets this when a second copy of the app runs on other ports.
const apiPort = process.env.TROVE_API_PORT ?? "8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    // The app calls /api/...; in development Vite forwards those requests to FastAPI.
    proxy: {
      "/api": {
        target: `http://127.0.0.1:${apiPort}`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  test: { environment: "jsdom", globals: true },
});
