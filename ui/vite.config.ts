import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  server: { port: 5174 },
  // The lazily loaded graph chunk is vis-network itself (about 170 kB gzipped); the main bundle stays small.
  build: { chunkSizeWarningLimit: 800 },
  test: {
    environment: "jsdom",
    setupFiles: ["src/test/setup.ts"],
  },
});
