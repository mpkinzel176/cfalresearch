# CFAL Website

Website for the **Computational Fluids and Aerodynamics Laboratory (CFAL)**,
Department of Aerospace Engineering, Embry-Riddle Aeronautical University,
directed by Dr. Michael P. Kinzel.

Built with [Astro](https://astro.build) + [Tailwind CSS v4](https://tailwindcss.com),
statically generated (no server required), deployable to Cloudflare Pages.

## Quick start

```bash
npm install
npm run dev       # http://localhost:4321
npm run build      # outputs to dist/
npm run preview    # serve the production build locally
```

## How content is organized

**Nothing you'll need to edit day-to-day lives inside a `.astro` component.**
All real content lives in structured data, so you can update the site without
touching React/Astro code:

```
src/data/
  people/
    faculty.json              Lab director(s)
    postdocs.json             Current postdoctoral scholars
    graduate_students.json    Current M.S./Ph.D. students
    undergraduate_students.json
    alumni.json                Everyone who has graduated/left
  research.json                The 7 major research areas
  projects.json                Sponsored research projects
  sponsors.json                Funders/collaborators (name + logo + url)
  publications-raw.json        Raw Google Scholar scrape (auto-refreshed)
  publications.json            Generated -- see scripts/build_publications.py
  review-needed.json           Flagged/uncertain items that need your input

src/content/news/*.md          News posts (Markdown, one file per post)
```

Cross-linking (a person's projects/publications, a project's team, a research
area's people/projects/publications) is **computed automatically** from these
files at build time (see `src/lib/data.ts`) -- you never need to maintain
those lists by hand.

## Common tasks

### Add a current student
Add an entry to the right file in `src/data/people/` (`graduate_students.json`
or `undergraduate_students.json`). Copy an existing entry's shape. Fields:

```json
{
  "id": "unique-kebab-case-slug",
  "name": "Full Name",
  "role": "Ph.D. Candidate",
  "degree": "Ph.D., Aerospace Engineering, Embry-Riddle Aeronautical University",
  "research_area": "One-line description of what they work on",
  "years": "2024–present",
  "photo": "",
  "linkedin": "",
  "personal_website": "",
  "google_scholar": "",
  "research_tags": ["hypersonics-reentry"]
}
```

`research_tags` should use the `id` values from `src/data/research.json`
(this is what powers the Research-area cross-linking). `photo` should be a
path under `public/` (e.g. `/people/jane-smith.jpg`) once you add the file.

### Move a student to Alumni
1. Cut their entry from `graduate_students.json` or `undergraduate_students.json`.
2. Paste it into `alumni.json`, renaming/adding fields to match that file's
   shape (`degree_level`, `university`, `thesis_title`, `thesis_url`,
   `current_position`, `current_employer`, etc. -- see existing entries).
3. If you have a verified dissertation/thesis link, add it as `thesis_url`.
   If you don't, leave it blank rather than guessing -- and consider adding a
   note to `review-needed.json`.

### Add a dissertation/thesis link
Add the `thesis_url` field to the person's entry in `alumni.json`. Only use a
direct link to the official record (ProQuest, an institutional repository
like `stars.library.ucf.edu` or `etda.libraries.psu.edu`, or a DOI) -- never a
search-results page.

### Add a publication
Publications are **not edited by hand**. They come from Google Scholar:

```bash
pwsh ./scripts/Fetch-GoogleScholarPublications.ps1   # refresh the raw scrape
python scripts/build_publications.py                  # regenerate publications.json
```

This also runs automatically every Monday via
`.github/workflows/update-publications.yml`. If you need to attach a DOI to a
publication, add a hand-verified entry to `DOI_MAP` in
`scripts/build_publications.py` (only ever copy a real DOI you've confirmed
-- never guess one from a pattern).

### Add a project
Add an entry to `src/data/projects.json`. `students`/`faculty` reference
`id`s from `src/data/people/*.json`; `research_areas` reference `id`s from
`src/data/research.json`; `keywords` are used to loosely match related
publications by title.

### Add a news story
Create a new Markdown file in `src/content/news/`, named
`YYYY-MM-short-slug.md`:

```markdown
---
date: 2026-03-15
headline: "Short headline"
summary: "One or two sentences shown on the News index."
category: "award"   # award | publication | grant | graduation | conference | media | new-member | other
---

Full story text in Markdown.
```

### Add a sponsor logo
Drop the logo file into `public/sponsors/` and set the `logo` field in
`src/data/sponsors.json` to that path (e.g. `/sponsors/nasa.png`). No funder
logos were available when this site was built -- see
`src/data/review-needed.json`.

## CV ingestion

`scripts/parse_cv.py` reads the PI's CV (`.docx`) in true document order and
groups every table under its preceding heading, writing
`scripts/cv_extract.json` for you to read through:

```bash
python scripts/parse_cv.py "/path/to/KinzelCV.docx"
```

It intentionally stops there rather than guessing how to reconcile
inconsistent or ambiguous rows (e.g. a student appearing in both a "current"
and "graduated" table with different data) into the site's JSON files --
that step takes a human read-through. See the script's docstring for details,
and `src/data/review-needed.json` for a log of judgment calls already flagged
during the initial build (including a caught copy/paste error in the source
CV's alumni table).

## Review needed

`src/data/review-needed.json` tracks every place information was uncertain,
unverifiable, or flagged during a link-verification pass, rather than
silently guessed. Check it periodically -- especially the LinkedIn and photo
gaps, which were deliberately left blank for every person rather than risk
misattributing a profile.

## Deployment (Cloudflare Pages)

1. Push this repository to GitHub/GitLab.
2. In the Cloudflare dashboard: **Workers & Pages → Create → Pages → Connect
   to Git**, select this repo.
3. Build settings:
   - Framework preset: **Astro**
   - Build command: `npm run build`
   - Build output directory: `dist`
4. Once you have a production URL (a `*.pages.dev` URL or a custom domain),
   update:
   - `site` in `astro.config.mjs`
   - the `Sitemap:` line in `public/robots.txt`

No environment variables or server-side infrastructure are required -- this
is a fully static site.

## Visitor analytics (where people are visiting from)

The site supports **Cloudflare Web Analytics** — free, cookieless (no consent
banner needed), and privacy-friendly. Its dashboard shows visitor **country**,
top pages, referrers, and traffic over time. It's built in but switched off
until you give it a token:

1. In the Cloudflare dashboard, go to **Analytics & Logs → Web Analytics →
   Add a site**. Enter your site's hostname (your `*.pages.dev` URL or custom
   domain) and choose the **manual JS snippet** option.
2. Cloudflare shows a snippet containing `"token": "abcdef..."`. Copy just
   that token value.
3. In your **Cloudflare Pages project → Settings → Environment variables**,
   add a variable named `PUBLIC_CF_ANALYTICS_TOKEN` with that value (set it
   for Production, and Preview too if you like), then redeploy.
4. (Optional, to test locally) copy `.env.example` to `.env` and paste the
   token there. `.env` is gitignored, so it won't be committed.

The token is public by design (it's visible in any page's HTML source), so
it's fine that it appears in the built site. Data appears in the dashboard
within a few minutes of the first real visit. With no token set, nothing
analytics-related is added to the pages at all.

## What's still a placeholder

- **Photos**: no student/staff photos were available; cards fall back to
  initials. Add files to `public/people/` and set each person's `photo` field.
- **LinkedIn**: left blank for everyone. Add directly to a person's
  `linkedin` field once confirmed -- avoid guessing, since a wrong link
  misattributes someone else's profile.
- **Sponsor logos**: no funder logo files were available; the homepage/about
  page render sponsor names as plain badges until logos are added.
- See `src/data/review-needed.json` for the full list, including a few
  dissertation titles that differ from the CV's working titles (verified
  against the official institutional repository) and one likely copy/paste
  error caught in the source CV.
