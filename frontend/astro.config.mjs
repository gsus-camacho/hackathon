import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import tailwind from "@astrojs/tailwind";
import node from "@astrojs/node";

export default defineConfig({
  output: "server",
  adapter: node({ mode: "standalone" }),
  server: { host: "0.0.0.0", port: 3000 },
  integrations: [react(), tailwind({ applyBaseStyles: false })],
  vite: {
    server: {
      allowedHosts: true,
      hmr: { clientPort: 443, protocol: "wss" },
    },
  },
});
