import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"
// import { inspectAttr } from 'kimi-plugin-inspect-react'

// https://vite.dev/config/
export default defineConfig({
  // Use '/' for root domain deployments (Vercel/Netlify)
  // Use './' for relative paths (works on both subpaths and custom domains)
  base: './',
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
