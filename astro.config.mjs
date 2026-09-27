import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';

// NOTE: "site" is a placeholder until this is deployed to a real domain.
// Update it (and public/robots.txt's Sitemap: line) once you know the
// production URL -- see README.md "Deployment" section.
export default defineConfig({
  site: 'https://cfal.erau.edu',
  output: 'static',
  integrations: [sitemap()],
  vite: {
    plugins: [tailwindcss()],
  },
});
