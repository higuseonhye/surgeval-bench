"""Prompt templates for a later VLM run. This module does not call a model."""

from __future__ import annotations

from surgeval.labels import PHASES, TOOLS

SYSTEM_ZERO_SHOT = """You answer questions about a single laparoscopic cholecystectomy frame.
Use only what is visible in the image.
If the frame is too dark, smoked, bloody, or otherwise unclear, answer abstain.
Do not give surgical advice, and do not invent instruments or anatomy that are not visible.
For a phase question, answer with exactly one of the listed phase names.
For a yes/no question, answer yes or no.
For a tool-count question, answer with an integer.
A tool is present only if at least half of its tip is visible."""

SYSTEM_FEW_SHOT = SYSTEM_ZERO_SHOT + """

Examples of phase names:
- Preparation: the gallbladder is being exposed before dissection of Calot's triangle.
- Calot triangle dissection: the cystic duct and cystic artery region is being dissected.
- Clipping and cutting: clips are applied and the duct or artery is divided.
- Gallbladder dissection: the gallbladder is separated from the liver bed.
- Gallbladder packaging: the specimen is placed in a bag.
- Cleaning and coagulation: the field is irrigated or bleeding points are coagulated.
- Gallbladder retraction: the gallbladder is pulled aside for exposure.

Tool-presence example:
Question: Is the hook present?
Answer: yes
Only count the hook when at least half of the tip is visible."""


def user_prompt(query: str, choices: list[str] | None = None) -> str:
    lines = [query.strip()]
    if choices:
        lines.append("Choices: " + " | ".join(choices))
    lines.append("Answer:")
    return "\n".join(lines)


def phase_choices() -> list[str]:
    return list(PHASES)


def tool_names() -> list[str]:
    return list(TOOLS)
