import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import tailwind from "@astrojs/tailwind";



import vercel from "@astrojs/vercel";

export default defineConfig({
  output: "server",
  adapter: vercel(),
  server: { host: "0.0.0.0", port: 3000 },
  integrations: [react(), tailwind({ applyBaseStyles: false })],
  vite: {
    server: {
      allowedHosts: true,
      hmr: { clientPort: 443, protocol: "wss" },
    },
  },
});