from dataclasses import dataclass
from typing import Optional


@dataclass
class ActivityScore:
    name: str
    display_name: Optional[str]
    display_order: int
    emoji_key: str
    kc: int
    points: int


@dataclass
class SkillScore:
    name: str
    display_name: Optional[str]
    display_order: int
    emoji_key: str
    xp: int
    level: int
    points: int


@dataclass
class ScoreBreakdown:
    skills: list[SkillScore]
    clues: list[ActivityScore]
    raids: list[ActivityScore]
    bosses: list[ActivityScore]


@dataclass
class NextPointProgress:
    category: str
    name: str
    display_name: Optional[str]
    emoji_key: str
    current: int
    points: int
    progress_percent: float
    remaining_to_next: int
    unit: str
