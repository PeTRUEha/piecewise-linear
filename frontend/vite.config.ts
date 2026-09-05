/** Конфигурация Vite для разработки и production-сборки. */

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const environment = loadEnv(mode, ".", "");
  const backendTarget = environment.VITE_BACKEND_TARGET || "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    server: {
      proxy: {
        "/api": backendTarget,
        "/docs": backendTarget,
        "/openapi.json": backendTarget,
      },
    },
  };
});
