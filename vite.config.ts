import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"
// import { inspectAttr } from 'kimi-plugin-inspect-react'

// https://vite.dev/config/
export default defineConfig({
  // Use '/' for root domain deployments (Vercel/Netlify)
  // Use './' only for subdirectory deployments
  base: '/lostbobo/',
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
