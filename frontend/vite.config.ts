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
          // 1. Supabase (separate as it's heavily used and relatively independent)
          if (id.includes("@supabase")) {
            return "vendor-supabase";
          }

          // 2. State management libraries (can be separate)
          if (
            id.includes("zustand") || 
            id.includes("jotai") || 
            id.includes("recoil") ||
            id.includes("redux")
          ) {
            return "vendor-state";
          }

          // 3. Everything else from node_modules goes into a single vendor chunk
          // This avoids circular dependencies between React and UI libraries
          if (id.includes("node_modules")) {
            return "vendor";
          }
        },
      },
    },
  },

  // Optional: Better sourcemaps for debugging production issues
  sourcemap: process.env.NODE_ENV === "development",
});
