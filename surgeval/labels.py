"""Closed label sets taken from the public Cholec80 annotation scheme.

Phase order follows Twinanda et al., IEEE TMI 2016 (EndoNet / Cholec80).
A tool is present only when at least half of its tip is visible.
"""

PHASES: tuple[str, ...] = (
    "Preparation",
    "Calot triangle dissection",
    "Clipping and cutting",
    "Gallbladder dissection",
    "Gallbladder packaging",
    "Cleaning and coagulation",
    "Gallbladder retraction",
)

TOOLS: tuple[str, ...] = (
    "grasper",
    "bipolar",
    "hook",
    "scissors",
    "clipper",
    "irrigator",
    "specimen bag",
)

# Longest alias first. Bare "dissection" is intentionally absent: Calot triangle
# dissection and gallbladder dissection must not collapse into one label.
PHASE_ALIASES: tuple[tuple[str, str], ...] = (
    ("calot triangle dissection", PHASES[1]),
    ("calottriangledissection", PHASES[1]),
    ("gallbladder dissection", PHASES[3]),
    ("gallbladderdissection", PHASES[3]),
    ("gallbladder packaging", PHASES[4]),
    ("gallbladderpackaging", PHASES[4]),
    ("gallbladder retraction", PHASES[6]),
    ("gallbladderretraction", PHASES[6]),
    ("clipping and cutting", PHASES[2]),
    ("clippingcutting", PHASES[2]),
    ("cleaning and coagulation", PHASES[5]),
    ("cleaningcoagulation", PHASES[5]),
    ("preparation", PHASES[0]),
    ("calot", PHASES[1]),
    ("clipping", PHASES[2]),
    ("packaging", PHASES[4]),
    ("retraction", PHASES[6]),
    ("coagulation", PHASES[5]),
    ("cleaning", PHASES[5]),
)

TOOL_ALIASES: dict[str, str] = {
    "grasper": "grasper",
    "bipolar": "bipolar",
    "hook": "hook",
    "scissors": "scissors",
    "clipper": "clipper",
    "clip applier": "clipper",
    "irrigator": "irrigator",
    "specimen bag": "specimen bag",
    "specimenbag": "specimen bag",
    "bag": "specimen bag",
}

YES_WORDS = {"yes", "y", "true", "present", "1"}
NO_WORDS = {"no", "n", "false", "absent", "0"}

FAILURE_LABELS: dict[str, str] = {
    "visual_occlusion": "시각적 차폐",
    "anatomical_ambiguity": "해부학적 모호성",
    "overconfidence_hallucination": "과신 환각",
    "temporal_inconsistency": "시간적 불일치",
    "unclassified_error": "미분류 오류",
}


def compact(text: str) -> str:
    lowered = text.strip().lower().replace("_", " ").replace("-", " ")
    return " ".join(lowered.split())


def canonical_phase(text: str) -> str | None:
    raw = compact(text)
    if raw.isdigit():
        index = int(raw)
        if 0 <= index < len(PHASES):
            return PHASES[index]
        return None
    squeezed = raw.replace(" ", "")
    for alias, name in PHASE_ALIASES:
        if raw == alias or squeezed == alias.replace(" ", ""):
            return name
    for alias, name in PHASE_ALIASES:
        if alias in raw:
            return name
    return None


def canonical_tool(text: str) -> str | None:
    raw = compact(text)
    return TOOL_ALIASES.get(raw) or TOOL_ALIASES.get(raw.replace(" ", ""))


def canonical_yes_no(text: str) -> str | None:
    raw = compact(text)
    if raw in YES_WORDS:
        return "yes"
    if raw in NO_WORDS:
        return "no"
    return None
