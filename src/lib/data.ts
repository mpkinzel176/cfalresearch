import faculty from '@/data/people/faculty.json';
import postdocs from '@/data/people/postdocs.json';
import graduateStudents from '@/data/people/graduate_students.json';
import undergraduateStudents from '@/data/people/undergraduate_students.json';
import alumni from '@/data/people/alumni.json';
import researchAreas from '@/data/research.json';
import projects from '@/data/projects.json';
import sponsors from '@/data/sponsors.json';
import publicationsData from '@/data/publications.json';

export type Person = {
  id: string;
  name: string;
  role?: string;
  degree?: string;
  degree_level?: string;
  university?: string;
  research_area?: string;
  years?: string;
  photo?: string;
  linkedin?: string;
  personal_website?: string;
  google_scholar?: string;
  thesis_title?: string;
  thesis_url?: string;
  thesis_url_note?: string;
  current_employer?: string;
  current_position?: string;
  funding?: string;
  note?: string;
  research_tags?: string[];
  [key: string]: unknown;
};

export type ResearchArea = {
  id: string;
  title: string;
  short_description: string;
  description: string;
  image?: string;
};

export type Project = {
  id: string;
  title: string;
  short_title: string;
  status: 'active' | 'completed';
  description: string;
  research_areas: string[];
  sponsor: string;
  collaborators: string[];
  students: string[];
  faculty: string[];
  keywords: string[];
  years: string;
  amount?: string;
};

export type Sponsor = { id: string; name: string; logo: string; url: string };

export type Publication = {
  year: number;
  authors: string[];
  title: string;
  journal: string;
  volume: string;
  pages: string;
  doi: string;
  url: string;
  scholar_url: string;
  research_tags: string[];
};

export const FACULTY = faculty as Person[];
export const POSTDOCS = postdocs as Person[];
export const GRADUATE_STUDENTS = graduateStudents as Person[];
export const UNDERGRADUATE_STUDENTS = undergraduateStudents as Person[];
export const ALUMNI = alumni as Person[];
export const RESEARCH_AREAS = researchAreas as ResearchArea[];
export const PROJECTS = projects as Project[];
export const SPONSORS = sponsors as Sponsor[];
export const PUBLICATIONS = (publicationsData as { publications: Publication[] }).publications;

export const ALL_CURRENT_PEOPLE: Person[] = [
  ...FACULTY,
  ...POSTDOCS,
  ...GRADUATE_STUDENTS,
  ...UNDERGRADUATE_STUDENTS,
];

export function personById(id: string): Person | undefined {
  return [...ALL_CURRENT_PEOPLE, ...ALUMNI].find((p) => p.id === id);
}

export function researchAreaById(id: string): ResearchArea | undefined {
  return RESEARCH_AREAS.find((r) => r.id === id);
}

export function projectById(id: string): Project | undefined {
  return PROJECTS.find((p) => p.id === id);
}

export function projectsForResearchArea(areaId: string): Project[] {
  return PROJECTS.filter((p) => p.research_areas.includes(areaId));
}

export function peopleForResearchArea(areaId: string): Person[] {
  return ALL_CURRENT_PEOPLE.filter((p) => p.research_tags?.includes(areaId));
}

export function publicationsForResearchArea(areaId: string): Publication[] {
  return PUBLICATIONS.filter((pub) => pub.research_tags.includes(areaId));
}

/** Loosely matches publications to a project via shared keywords in the title. */
export function publicationsForProject(project: Project): Publication[] {
  const keywords = project.keywords.map((k) => k.toLowerCase());
  return PUBLICATIONS.filter((pub) => {
    const title = pub.title.toLowerCase();
    return keywords.some((kw) => title.includes(kw));
  });
}

export function projectsForPerson(personId: string): Project[] {
  return PROJECTS.filter((p) => p.students.includes(personId) || p.faculty.includes(personId));
}

export function peopleForProject(project: Project): Person[] {
  const ids = new Set([...project.students, ...project.faculty]);
  return [...ALL_CURRENT_PEOPLE, ...ALUMNI].filter((p) => ids.has(p.id));
}

/** Matches a person to publications via "initial + surname" against the
 * abbreviated author strings scraped from Google Scholar (e.g. "M Kinzel"). */
export function publicationsForPerson(person: Person, limit = 10): Publication[] {
  const parts = person.name.split(' ').filter(Boolean);
  if (parts.length < 2) return [];
  const surname = parts[parts.length - 1].toLowerCase();
  const initial = parts[0][0]?.toLowerCase();
  const matches = PUBLICATIONS.filter((pub) =>
    pub.authors.some((a) => {
      const aParts = a.toLowerCase().replace(/\./g, '').split(' ').filter(Boolean);
      if (aParts.length === 0) return false;
      const aSurname = aParts[aParts.length - 1];
      const aInitial = aParts[0][0];
      return aSurname === surname && aInitial === initial;
    })
  );
  return matches.slice(0, limit);
}

export function sponsorByName(name: string): Sponsor | undefined {
  const lower = name.toLowerCase();
  return SPONSORS.find((s) => lower.includes(s.name.toLowerCase()) || lower.includes(s.id));
}

export type ThesisEntry = {
  personId: string;
  name: string;
  degree_level: string;
  university: string;
  title: string;
  url: string;
  year: number;
  linkedin?: string;
  research_tags: string[];
};

function endYear(years: string | undefined): number {
  if (!years) return 0;
  const matches = years.match(/\d{4}/g);
  if (!matches) return 0;
  return parseInt(matches[matches.length - 1], 10);
}

export function allTheses(): ThesisEntry[] {
  const entries: ThesisEntry[] = ALUMNI.filter((p) => p.thesis_title).map((p) => ({
    personId: p.id,
    name: p.name,
    degree_level: (p.degree_level as string) ?? '',
    university: (p.university as string) ?? '',
    title: p.thesis_title as string,
    url: (p.thesis_url as string) ?? '',
    year: endYear(p.years),
    linkedin: p.linkedin as string | undefined,
    research_tags: p.research_tags ?? [],
  }));
  return entries.sort((a, b) => b.year - a.year);
}

export function slugify(input: string): string {
  return input
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}
