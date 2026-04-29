import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  define: {
    "import.meta.env.VITE_API_BASE_URL": JSON.stringify("http://13.204.14.38:8000"),
  },
});