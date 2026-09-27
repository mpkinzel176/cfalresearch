import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const news = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/news' }),
  schema: z.object({
    date: z.date(),
    headline: z.string(),
    summary: z.string(),
    category: z.enum([
      'award', 'publication', 'grant', 'graduation', 'conference', 'media', 'new-member', 'other',
    ]).default('other'),
    image: z.string().optional(),
    external_link: z.string().optional(),
  }),
});

export const collections = { news };
