import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: process.env.NODE_ENV === "production" ? "/HealthcareAI-NorthAfrica---Antigravity/" : "/",
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.js",
    globals: true,
    css: true,
    restoreMocks: true,
    clearMocks: true
  },
  server: {
    port: 3000,
    strictPort: true
  }
});
