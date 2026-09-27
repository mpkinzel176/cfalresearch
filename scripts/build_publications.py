"""
Builds src/data/publications.json from src/data/publications-raw.json
(the Google Scholar scrape refreshed by scripts/Fetch-GoogleScholarPublications.ps1).

What it does:
  - Splits the scraped "authors" string into an array.
  - Splits "venue" into journal/conference name + volume/pages where the
    Scholar-scraped string follows a recognizable "Name N (n), pages, year" pattern.
  - Attaches a DOI ONLY when a confident title match is found in DOI_MAP below.
    DOI_MAP is hand-curated from the CV's own "List of Publications" section,
    which lists real DOIs for many 2019-2026 journal articles. We never guess
    or construct a DOI from a title/journal name.
  - Assigns research_tags via keyword matching on the title (heuristic; not
    guaranteed exhaustive -- meant to power cross-linking, not as ground truth).

Run: python scripts/build_publications.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "src" / "data" / "publications-raw.json"
OUT = ROOT / "src" / "data" / "publications.json"

# Hand-curated from the CV's explicit "Refereed Journal Articles" list, where a
# literal "https://doi.org/10...." string was printed alongside the citation.
# Matched by a short, distinctive substring of the title (case-insensitive).
# ONLY add a pair here when the DOI is copied verbatim from the CV (or another
# verified source) -- never a pattern-guessed or reconstructed DOI. Every other
# publication is left without a DOI rather than risk a wrong link.
DOI_MAP = {
    "thrust and power characterization of a dual-domain aquatic": "10.1016/j.oceaneng.2025.122060",
    "geometrical comparison of inline and staggered stack wire mesh": "10.1016/j.csite.2024.105729",
    "sprayed liquid flaps: a numerical assessment of a multiphase jet": "10.2514/1.C037850",
    "evaluation of molten sand, dust, and ash infiltrating thermal barrier": "10.1063/5.0234882",
    "a numerical assessment of shock": "10.1063/5.0136536",
    "onto quantifying unsteady propulsion characteristics": "10.1115/1.4057036",
    "the effect of omega-9 on bone viscoelasticity": "10.3390/nu15051209",
}

TAG_RULES = [
    ("rotorcraft-advanced-air-mobility", [
        "rotor", "airwake", "coaxial", "helicopter", "uav", "uas", "vertiport",
        "ground effect", "outwash", "fanwing", "perching", "propeller",
    ]),
    ("space-planetary-aerodynamics", [
        "dragonfly", "titan", "microgravity", "lunar", "regolith", "space",
        "cislunar", "orbit", "in-space manufacturing", "osteoporosis", "bone",
    ]),
    ("hypersonics-reentry", [
        "hypersonic", "reentry", "re-entry", "heatshield", "heat shield",
        "thermal protection", "backshell", "aeroshell", "transpiration cooling",
        "thermal barrier coating", "cmas",
    ]),
    ("multiphase-extreme-environment-flows", [
        "droplet", "cavitation", "shock-droplet", "raindrop", "icing", "ice",
        "saltation", "breakup", "multiphase", "spray", "jet", "combustion",
        "aluminum", "particle",
    ]),
    ("atmospheric-environmental-flows", [
        "atmospheric", "boundary layer", "wind turbine", "airborne transmission",
        "saliva", "sneeze", "covid", "airwake", "wind-turbine", "urban",
    ]),
    ("real-time-ai-accelerated-modeling", [
        "machine learning", "neural network", "pinn", "physics-informed",
        "surrogate", "gaussian process", "reduced order", "data-driven",
        "optimization of logistical",
    ]),
    ("multidisciplinary-design", [
        "optimization", "design optimization", "multidisciplinary", "supply chain",
        "logistical", "cargo",
    ]),
]


def split_authors(raw: str) -> list[str]:
    raw = raw.strip()
    truncated = raw.endswith("...") or raw.endswith("…")
    raw = raw.rstrip(".").rstrip("…").strip()
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if truncated and parts:
        parts.append("et al.")
    return parts


def parse_venue(venue: str, year: int) -> dict:
    venue = (venue or "").strip()
    if not venue:
        return {"journal": "", "volume": "", "pages": ""}
    # Strip a trailing ", <year>" if present (redundant with the year field)
    venue = re.sub(rf",?\s*{year}$", "", venue).strip()
    # Try "Journal Name N (n), pages" pattern
    m = re.match(r"^(.*?)\s+(\d+)\s*\((\d+)\),\s*([\d\-–]+)$", venue)
    if m:
        return {"journal": m.group(1).strip(), "volume": m.group(2), "pages": m.group(4)}
    m = re.match(r"^(.*?)\s+(\d+),\s*([\w\d\-–]+)$", venue)
    if m:
        return {"journal": m.group(1).strip(), "volume": m.group(2), "pages": m.group(3)}
    return {"journal": venue, "volume": "", "pages": ""}


def tag_title(title: str) -> list[str]:
    lower = title.lower()
    tags = []
    for tag, keywords in TAG_RULES:
        if any(kw in lower for kw in keywords):
            tags.append(tag)
    return tags


def find_doi(title: str) -> str:
    lower = title.lower()
    for key, doi in DOI_MAP.items():
        if key in lower:
            return doi
    return ""


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8-sig"))
    out = []
    for item in raw["publications"]:
        venue_parts = parse_venue(item.get("venue", ""), item["year"])
        doi = find_doi(item["title"])
        out.append({
            "year": item["year"],
            "authors": split_authors(item["authors"]),
            "title": item["title"],
            "journal": venue_parts["journal"],
            "volume": venue_parts["volume"],
            "pages": venue_parts["pages"],
            "doi": doi,
            "url": (f"https://doi.org/{doi}" if doi else item.get("url", "")),
            "scholar_url": item.get("url", ""),
            "research_tags": tag_title(item["title"]),
        })
    out.sort(key=lambda p: p["year"], reverse=True)
    OUT.write_text(json.dumps({
        "source": raw.get("source"),
        "refreshedAt": raw.get("refreshedAt"),
        "publications": out,
    }, indent=2), encoding="utf-8")
    print(f"Wrote {len(out)} publications to {OUT}")


if __name__ == "__main__":
    main()
