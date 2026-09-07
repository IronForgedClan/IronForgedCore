import json
import logging
from typing import List, NotRequired, Type, TypedDict, TypeVar, cast

T = TypeVar("T", bound=TypedDict)
logger = logging.getLogger(__name__)


class XpRateBucket(TypedDict):
    end_xp: int  # exclusive upper bound; bucket applies when skill_xp < end_xp
    rate: float  # xp/hour within this bracket


class Skill(TypedDict):
    name: str
    display_order: int
    emoji_key: str
    xp_per_point: int
    xp_per_point_post_99: int
    xp_per_hour: NotRequired[List[XpRateBucket]]


class Activity(TypedDict):
    name: str
    display_name: NotRequired[str]
    display_order: int
    emoji_key: str
    kc_per_point: int
    kc_per_hour: NotRequired[float]


SKILLS: List[Skill] | None = None
CLUES: List[Activity] | None = None
RAIDS: List[Activity] | None = None
BOSSES: List[Activity] | None = None


def load_json_data(file_name: str, type: Type[T]) -> List[T]:
    with open(file_name, "r") as file:
        logger.debug(f"Reading file: {file_name}")
        data = json.load(file)

        if not isinstance(data, list):
            raise TypeError(f"{file_name}: does not contain an array/list")

        for item in data:
            if not isinstance(item, dict):
                raise TypeError(f"{file_name}: does not contain object/dict")

            for key in type.__annotations__.keys():
                if key not in item and key in type.__optional_keys__:
                    item[key] = None
                elif key not in item:
                    raise KeyError(
                        f"{file_name}: object missing key ({key}) for type ({type.__name__})"
                    )

        output = cast(List[T], data)
        if output is None or len(output) < 1:
            raise ValueError(f"{file_name}: output result is invalid")

        return output


def set_data(
    *,
    skills: List[Skill] | None = None,
    clues: List[Activity] | None = None,
    raids: List[Activity] | None = None,
    bosses: List[Activity] | None = None,
) -> None:
    """Populate module-level data constants. Called by consumers at startup
    and by tests in setUp(). No-op for kwargs left as None."""
    global SKILLS, CLUES, RAIDS, BOSSES
    if skills is not None:
        SKILLS = skills
    if clues is not None:
        CLUES = clues
    if raids is not None:
        RAIDS = raids
    if bosses is not None:
        BOSSES = bosses


def load_and_set(data_dir: str = "data") -> None:
    """Load skills.json, bosses.json, clues.json, raids.json from `data_dir`
    and call set_data(). Used by consumer apps at startup."""
    set_data(
        skills=load_json_data(f"{data_dir}/skills.json", Skill),
        clues=load_json_data(f"{data_dir}/clues.json", Activity),
        raids=load_json_data(f"{data_dir}/raids.json", Activity),
        bosses=load_json_data(f"{data_dir}/bosses.json", Activity),
    )
