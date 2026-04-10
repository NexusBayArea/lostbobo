import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/",
  plugins: [react()],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  build: {
    // Reasonable limit — 1000kB is acceptable for most apps
    chunkSizeWarningLimit: 1000,

    rollupOptions: {
      output: {
        manualChunks: (id: string) => {
          // 1. Core React + Router (very stable)
          if (id.includes("react") || id.includes("react-dom") || id.includes("react-router")) {
            return "vendor-react";
          }

          // 2. Supabase (you use it heavily)
          if (id.includes("@supabase")) {
            return "vendor-supabase";
          }

          // 3. State management (Zustand, etc.)
          if (id.includes("zustand") || id.includes("jotai") || id.includes("recoil")) {
            return "vendor-state";
          }

          // 4. UI / Charts / Heavy visuals (common culprits in dashboards)
          if (
            id.includes("recharts") ||
            id.includes("chart.js") ||
            id.includes("framer-motion") ||
            id.includes("lucide-react") ||
            id.includes("sonner") ||
            id.includes("@radix-ui")
          ) {
            return "vendor-ui";
          }

          // 5. Everything else from node_modules goes into a general vendor chunk
          if (id.includes("node_modules")) {
            return "vendor";
          }
        },
      },
    },
  },
});
