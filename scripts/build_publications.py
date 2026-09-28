"""
Builds src/data/publications.json from src/data/publications-raw.json
(the Google Scholar scrape refreshed by scripts/Fetch-GoogleScholarPublications.ps1,
which now pulls Dr. Kinzel's full publication history, not just recent years).

What it does:
  - Splits the scraped "authors" string into an array.
  - Canonicalizes the scraped "venue" string into a clean "journal" name used
    for grouping/filtering (e.g. every "AIAA SCITECH 2025 Forum, 1922" /
    "AIAA Scitech 2020 Forum, 1783" / etc. collapses to one "AIAA SciTech
    Forum" entry, and "AIP advances" / "AIP Advances" collapse to one
    consistently-cased entry) while keeping the original full venue string
    (with paper/article number) as "venue_detail" so nothing is lost.
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
        "rotorcraft", "blade",
    ]),
    ("space-planetary-aerodynamics", [
        "dragonfly", "titan", "microgravity", "lunar", "regolith", "space",
        "cislunar", "orbit", "in-space manufacturing", "osteoporosis", "bone",
        "planetary", "extraterrestrial", "astronaut",
    ]),
    ("hypersonics-reentry", [
        "hypersonic", "reentry", "re-entry", "heatshield", "heat shield",
        "thermal protection", "backshell", "aeroshell", "transpiration cooling",
        "thermal barrier coating", "cmas", "supersonic", "high-speed vehicle",
        "entry capsule", "ballistic",
    ]),
    ("multiphase-extreme-environment-flows", [
        "droplet", "cavitat", "shock-droplet", "raindrop", "icing", r"\bice\b",
        r"\bice-", "saltation", "breakup", "multiphase", "spray", "jet",
        "combustion", "aluminum", "particle", "bubble", "two-phase",
        "supercavitat", "water entry", "sloshing", "slosh", "gas entrainment",
        "quenched", "granular", "proppant", "cmas",
    ]),
    ("atmospheric-environmental-flows", [
        "atmospheric", "boundary layer", "wind turbine", "airborne transmission",
        "saliva", "sneeze", "covid", "airwake", "wind-turbine", "urban",
        "wind energy", "turbulence", "ship airwake",
    ]),
    ("real-time-ai-accelerated-modeling", [
        "machine learning", "neural network", "pinn", "physics-informed",
        "surrogate", "gaussian process", "reduced order", "data-driven",
        "optimization of logistical", "real-time", "digital twin",
        "lattice-boltzmann", "lattice boltzmann",
    ]),
    ("multidisciplinary-design", [
        "optimization", "design optimization", "multidisciplinary", "supply chain",
        "logistical", "cargo", "verification and validation", "uncertainty quantification",
    ]),
]

# Any substring match (case-insensitive, checked against the de-yeared venue
# string) short-circuits to this canonical conference/meeting name. Order
# matters -- more specific patterns should come first. This is what makes
# "AIAA SCITECH 2026 Forum, 1736" and "AIAA Scitech 2020 Forum, 1783" group
# together as one "AIAA SciTech Forum" entry instead of two, etc.
CONFERENCE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"AIAA\s+SCI\s*TECH", re.I), "AIAA SciTech Forum"),
    (re.compile(r"AIAA\s+Science and Technology Forum", re.I), "AIAA SciTech Forum"),
    (re.compile(r"AIAA\s+AVIATION", re.I), "AIAA AVIATION Forum"),
    (re.compile(r"AIAA\s+Aerospace Sciences Meeting", re.I), "AIAA Aerospace Sciences Meeting"),
    (re.compile(r"AIAA\s+Fluid Dynamics Conference", re.I), "AIAA Fluid Dynamics Conference"),
    (re.compile(r"AIAA\s+Theoretical Fluid Mechanics Conference", re.I), "AIAA Theoretical Fluid Mechanics Conference"),
    (re.compile(r"AIAA\s+Atmospheric and Space Environments Conference", re.I), "AIAA Atmospheric and Space Environments Conference"),
    (re.compile(r"AIAA\s+International Space Planes and Hypersonic", re.I), "AIAA International Space Planes and Hypersonic Systems and Technologies Conference"),
    (re.compile(r"AIAA\s+CFD (Meeting|Conference)|AIAA\s+Computational Fluid Dynamics Conference", re.I), "AIAA Computational Fluid Dynamics Conference"),
    (re.compile(r"Annual Meeting of the (APS )?Division of Fluid Dynamics", re.I), "APS Division of Fluid Dynamics (DFD)"),
    (re.compile(r"APS Division of Fluid Dynamics Meeting Abstracts", re.I), "APS Division of Fluid Dynamics (DFD)"),
    (re.compile(r"Bulletin of the American Physical Society", re.I), "APS Division of Fluid Dynamics (DFD)"),
    (re.compile(r"Fluids Engineering Division Summer Meeting|\bFEDSM\b", re.I), "ASME Fluids Engineering Division Summer Meeting (FEDSM)"),
    (re.compile(r"International Mechanical Engineering Congress", re.I), "ASME International Mechanical Engineering Congress (IMECE)"),
    (re.compile(r"Verification and Validation Symposium|\bV&V\d", re.I), "ASME Verification and Validation Symposium"),
    (re.compile(r"International Symposium on Cavitation", re.I), "International Symposium on Cavitation (CAV)"),
    (re.compile(r"Symposium on Marine Propulsors", re.I), "International Symposium on Marine Propulsors"),
    (re.compile(r"International Conference on Nuclear Engineering", re.I), "International Conference on Nuclear Engineering (ICONE)"),
    (re.compile(r"International Astronautical (Congress|Federation)", re.I), "International Astronautical Congress (IAC)"),
    (re.compile(r"American Astronomical Society", re.I), "American Astronomical Society (AAS) Meeting"),
    (re.compile(r"Transport Phenomena and Dynamics of Rotating Machinery|\bISROMAC\b", re.I), "ISROMAC"),
    (re.compile(r"Vertical Flight Society|\bAHS\b.*Forum|Annual Forum Proceedings.*AHS", re.I), "Vertical Flight Society (AHS) Forum"),
    (re.compile(r"North American Masonry Conference", re.I), "North American Masonry Conference"),
    (re.compile(r"OpenFOAM Workshop", re.I), "OpenFOAM Workshop"),
    (re.compile(r"North American Mixing Forum", re.I), "North American Mixing Forum"),
    (re.compile(r"LPI Contributions|Lunar and Planetary", re.I), "Lunar and Planetary Institute (LPI) Contributions"),
]


def split_authors(raw: str) -> list[str]:
    raw = raw.strip()
    truncated = raw.endswith("...") or raw.endswith("…")
    raw = raw.rstrip(".").rstrip("…").strip()
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if truncated and parts:
        parts.append("et al.")
    return parts


def strip_year(venue: str, year: int) -> str:
    venue = re.sub(rf",?\s*{year}$", "", venue).strip()
    venue = re.sub(rf"^{year}\s+", "", venue).strip()
    return venue


# A few journals Google Scholar scrapes with inconsistent capitalization often
# enough that the "most uppercase letters wins" heuristic in main() still
# picks an awkward variant. Override those explicitly (lowercase key -> the
# correct display form).
CANONICAL_CASING_OVERRIDES = {
    "bone research": "Bone Research",
    "journal of visualized experiments": "Journal of Visualized Experiments",
    "aiaa journal": "AIAA Journal",
}


def generic_journal_name(stripped: str) -> str:
    """Best-effort extraction of a bare journal/conference name from a venue
    string that isn't a recognized conference pattern, e.g.
    'Physics of Fluids 36 (11)' -> 'Physics of Fluids',
    'Ocean Engineering 339, 122060' -> 'Ocean Engineering',
    'Journal of Aircraft, 1-12' -> 'Journal of Aircraft'."""
    m = re.match(
        r"^(?:\d+(?:st|nd|rd|th)\s+)?([A-Za-z][A-Za-z&.:’'\- ]*?)(?=\s+\d|\s*,|\s*$)",
        stripped,
    )
    if m:
        name = m.group(1).strip().rstrip(",").strip()
        if name:
            return name
    return stripped


def canonicalize_venue(venue: str, year: int) -> tuple[str, str]:
    """Returns (canonical_key_name, full_original_venue)."""
    full = (venue or "").strip()
    if not full:
        return "", ""
    stripped = strip_year(full, year)
    if not stripped:
        return "", full
    for pattern, label in CONFERENCE_PATTERNS:
        if pattern.search(stripped):
            return label, full
    return generic_journal_name(stripped), full


def keyword_matches(keyword: str, lower_title: str) -> bool:
    if keyword.startswith(r"\b"):
        return re.search(keyword, lower_title) is not None
    return keyword in lower_title


def tag_title(title: str) -> list[str]:
    lower = title.lower()
    tags = []
    for tag, keywords in TAG_RULES:
        if any(keyword_matches(kw, lower) for kw in keywords):
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

    # Pass 1: canonicalize every venue and track the "best-cased" display
    # variant per lowercase key (Google Scholar scrapes are inconsistently
    # cased, e.g. "AIP advances" vs "AIP Advances" -- prefer whichever
    # variant has more capital letters as a simple proxy for correct casing).
    prepared = []
    best_casing: dict[str, str] = {}
    for item in raw["publications"]:
        canonical, full_venue = canonicalize_venue(item.get("venue", ""), item["year"])
        key = canonical.lower()
        if key:
            current = best_casing.get(key)
            if current is None or sum(c.isupper() for c in canonical) > sum(c.isupper() for c in current):
                best_casing[key] = canonical
        prepared.append((item, canonical.lower(), full_venue))

    out = []
    for item, journal_key, full_venue in prepared:
        journal = CANONICAL_CASING_OVERRIDES.get(journal_key, best_casing.get(journal_key, ""))
        doi = find_doi(item["title"])
        out.append({
            "year": item["year"],
            "authors": split_authors(item["authors"]),
            "title": item["title"],
            "journal": journal,
            "venue_detail": full_venue,
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
    print(f"Distinct journal/conference groups: {len({p['journal'] for p in out if p['journal']})}")


if __name__ == "__main__":
    main()
