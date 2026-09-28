import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';

// Canonical production URL. If it changes, also update the Sitemap: line in
// public/robots.txt -- see README.md "Deployment" section.
export default defineConfig({
  site: 'https://www.cfalresearch.com',
  output: 'static',
  integrations: [sitemap()],
  vite: {
    plugins: [tailwindcss()],
  },
});
