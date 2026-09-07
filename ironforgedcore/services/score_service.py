import logging
import math

from ironforgedcore.cache.score_cache import SCORE_CACHE
from ironforgedcore.common.normalize import normalize_discord_string
from ironforgedcore.common.logging_utils import log_api_call
from ironforgedcore.common.ranks import RANK, get_rank_from_points
from ironforgedcore.exceptions.score_exceptions import HiscoresError, HiscoresNotFound
from ironforgedcore.http import AsyncHttpClient, HttpResponse
from ironforgedcore.models.score import (
    ActivityScore,
    NextPointProgress,
    ScoreBreakdown,
    SkillScore,
)
from ironforgedcore.storage import data as data_module

logger = logging.getLogger(__name__)

# Global service instances to avoid recreation
_score_service_instance = None


def _find_bucket_rate(buckets: list[dict] | None, current_xp: int) -> float | None:
    """Return the rate for the XP bucket containing ``current_xp``"""
    if not buckets:
        return None
    for bucket in buckets:
        if current_xp < bucket["end_xp"]:
            return float(bucket["rate"])
    return float(buckets[-1]["rate"])


# Entries that are unrealistic to sustain kph so are excluded from point_progress
EXCLUDED_ITEMS: set[str] = {"Mimic", "Hespori", "Skotizo"}


class ScoreService:
    def __init__(self, http: AsyncHttpClient) -> None:
        self.http: AsyncHttpClient = http
        self.hiscores_url: str = (
            "https://secure.runescape.com/m=hiscore_oldschool/"
            "index_lite.json?player={rsn}"
        )
        self.level_99_xp: int = 13_034_431

    async def get_player_score(
        self, player_name: str, bypass_cache: bool | None = False
    ) -> ScoreBreakdown:
        normalized_name: str = normalize_discord_string(input=player_name)
        breakdown: ScoreBreakdown | None = await SCORE_CACHE.get(normalized_name)

        if not breakdown or bypass_cache:
            data: HttpResponse = await self.http.get(
                self.hiscores_url.format(rsn=normalized_name)
            )

            if data["status"] == 404:
                raise HiscoresNotFound()

            if data["status"] != 200:
                raise HiscoresError(
                    message=f"Unexpected response code {data['status']}"
                )

            skills: list[SkillScore] = self._process_skills(data["body"])
            clues, raids, bosses = self._process_activities(data["body"])

            breakdown = ScoreBreakdown(skills, clues, raids, bosses)
            await SCORE_CACHE.set(normalized_name, breakdown)

        assert breakdown is not None
        return breakdown

    def _process_skills(self, score_data) -> list[SkillScore]:
        skills = data_module.SKILLS
        if skills is None or score_data is None or score_data["skills"] is None:
            raise RuntimeError("Unable to read skills data")

        output = []

        for skill_data in score_data["skills"]:
            skill_name = skill_data["name"]

            if skill_name.lower() == "overall":
                continue

            skill = next(
                (skill for skill in skills if skill["name"] == skill_name), None
            )

            if skill is None:
                continue

            skill_level = (
                int(skill_data["level"]) if int(skill_data["level"]) > 1 else 1
            )
            experience = int(skill_data["xp"]) if int(skill_data["xp"]) > 0 else 0

            if skill_level < 99:
                points = int(experience / skill["xp_per_point"])
            else:
                points = int(self.level_99_xp / skill["xp_per_point"]) + int(
                    (experience - self.level_99_xp) / skill["xp_per_point_post_99"]
                )

            data: SkillScore = SkillScore(
                name=skill["name"],
                display_name=None,
                display_order=skill["display_order"],
                emoji_key=skill["emoji_key"],
                level=skill_level,
                xp=experience,
                points=points,
            )

            output.append(data)

        return output

    def _process_activities(
        self,
        score_data,
    ) -> tuple[list[ActivityScore], list[ActivityScore], list[ActivityScore]]:
        clues_config = data_module.CLUES
        bosses_config = data_module.BOSSES
        raids_config = data_module.RAIDS
        if clues_config is None or bosses_config is None or raids_config is None:
            raise RuntimeError("Unable to read activity data")

        clues = []
        raids = []
        bosses = []

        for activity in score_data["activities"]:
            activity_name = activity["name"]

            clue = next(
                (clue for clue in clues_config if clue["name"] == activity_name), None
            )
            if clue is not None:
                kc = max(int(activity["score"]), 0)
                data = ActivityScore(
                    name=clue["name"],
                    display_name=None,
                    display_order=clue["display_order"],
                    emoji_key=clue["emoji_key"],
                    kc=kc,
                    points=max(int(kc / clue["kc_per_point"]), 0),
                )

                if clue.get("display_name", None) is not None:
                    data.display_name = clue.get("display_name", "")

                clues.append(data)
                continue

            raid = next(
                (raid for raid in raids_config if raid["name"] == activity_name), None
            )
            if raid is not None:
                kc = max(int(activity["score"]), 0)

                data = ActivityScore(
                    name=raid["name"],
                    display_name=None,
                    display_order=raid["display_order"],
                    emoji_key=raid["emoji_key"],
                    kc=kc,
                    points=max(int(kc / raid["kc_per_point"]), 0),
                )

                if raid.get("display_name", None) is not None:
                    data.display_name = raid.get("display_name", "")

                raids.append(data)
                continue

            boss = next(
                (boss for boss in bosses_config if boss["name"] == activity_name), None
            )
            if boss is not None:
                kc = max(int(activity["score"]), 0)

                if kc < 1:
                    continue

                data = ActivityScore(
                    name=boss["name"],
                    display_name=None,
                    display_order=boss["display_order"],
                    emoji_key=boss["emoji_key"],
                    kc=kc,
                    points=max(int(kc / boss["kc_per_point"]), 0),
                )

                if boss.get("display_name", None) is not None:
                    data.display_name = boss.get("display_name", "")

                bosses.append(data)
                continue

        return clues, raids, bosses

    async def get_proximity_to_next_point(
        self, breakdown: ScoreBreakdown, limit: int = 10
    ) -> list[NextPointProgress]:
        """Return items ranked by shortest real time to the next point.

        Each item is a SkillScore or ActivityScore from the breakdown. Items
        with no progress (0 XP / 0 KC) are excluded. Skills above level 99
        use the post-99 XP threshold.

        ``time_hours`` is computed per entry as ``remaining / rate`` when
        a positive rate is available, else ``None``. For skills, the rate is
        resolved from the tiered ``config["xp_per_hour"]`` bucket list by
        selecting the bucket whose ``end_xp`` exceeds the player's current
        XP. Activities use a single ``config["kc_per_hour"]``.
        """
        results: list[NextPointProgress] = []

        skills = data_module.SKILLS or []
        for skill in breakdown.skills:
            if skill.xp <= 0:
                continue

            config = next((s for s in skills if s["name"] == skill.name), None)
            if config is None:
                continue

            if config.get("name") in EXCLUDED_ITEMS:
                continue

            if skill.xp < self.level_99_xp:
                bucket = config["xp_per_point"]
                current_point = skill.xp // bucket
                next_threshold = (current_point + 1) * bucket
            else:
                bucket = config["xp_per_point_post_99"]
                post_99_xp = skill.xp - self.level_99_xp
                post_99_point = post_99_xp // bucket
                next_threshold = self.level_99_xp + (post_99_point + 1) * bucket

            raw_remaining = next_threshold - skill.xp
            if raw_remaining <= 0:
                continue

            # Players gain at minimum 1xp per action- ceil so the displayed
            # remaining and the time estimate describe the same quantity
            remaining = math.ceil(raw_remaining)

            buckets = config.get("xp_per_hour")
            rate = _find_bucket_rate(buckets, skill.xp)
            time_hours = remaining / rate if rate and rate > 0 else None

            results.append(
                NextPointProgress(
                    category="skill",
                    name=skill.name,
                    display_name=None,
                    emoji_key=skill.emoji_key,
                    current=skill.xp,
                    points=skill.points,
                    progress_percent=1 - (raw_remaining / bucket),
                    remaining_to_next=remaining,
                    unit="xp",
                    time_hours=time_hours,
                )
            )

        bosses = data_module.BOSSES or []
        for boss in breakdown.bosses:
            if boss.kc <= 0:
                continue

            config = next((b for b in bosses if b["name"] == boss.name), None)
            if config is None:
                continue

            if config.get("name") in EXCLUDED_ITEMS:
                continue

            bucket = config["kc_per_point"]
            next_threshold = (boss.points + 1) * bucket
            raw_remaining = next_threshold - boss.kc
            if raw_remaining <= 0:
                continue

            remaining = math.ceil(raw_remaining)

            kc_per_hour = config.get("kc_per_hour")
            time_hours = (
                remaining / kc_per_hour if kc_per_hour and kc_per_hour > 0 else None
            )

            results.append(
                NextPointProgress(
                    category="boss",
                    name=boss.name,
                    display_name=boss.display_name,
                    emoji_key=boss.emoji_key,
                    current=boss.kc,
                    points=boss.points,
                    progress_percent=1 - (raw_remaining / bucket),
                    remaining_to_next=remaining,
                    unit="kc",
                    time_hours=time_hours,
                )
            )

        raids = data_module.RAIDS or []
        for raid in breakdown.raids:
            if raid.kc <= 0:
                continue

            config = next((r for r in raids if r["name"] == raid.name), None)
            if config is None:
                continue

            if config.get("name") in EXCLUDED_ITEMS:
                continue

            bucket = config["kc_per_point"]
            next_threshold = (raid.points + 1) * bucket
            raw_remaining = next_threshold - raid.kc
            if raw_remaining <= 0:
                continue

            remaining = math.ceil(raw_remaining)

            kc_per_hour = config.get("kc_per_hour")
            time_hours = (
                remaining / kc_per_hour if kc_per_hour and kc_per_hour > 0 else None
            )

            results.append(
                NextPointProgress(
                    category="raid",
                    name=raid.name,
                    display_name=raid.display_name,
                    emoji_key=raid.emoji_key,
                    current=raid.kc,
                    points=raid.points,
                    progress_percent=1 - (raw_remaining / bucket),
                    remaining_to_next=remaining,
                    unit="kc",
                    time_hours=time_hours,
                )
            )

        clues = data_module.CLUES or []
        for clue in breakdown.clues:
            if clue.kc <= 0:
                continue

            config = next((c for c in clues if c["name"] == clue.name), None)
            if config is None:
                continue

            if config.get("name") in EXCLUDED_ITEMS:
                continue

            bucket = config["kc_per_point"]
            next_threshold = (clue.points + 1) * bucket
            raw_remaining = next_threshold - clue.kc
            if raw_remaining <= 0:
                continue

            remaining = math.ceil(raw_remaining)

            kc_per_hour = config.get("kc_per_hour")
            time_hours = (
                remaining / kc_per_hour if kc_per_hour and kc_per_hour > 0 else None
            )

            results.append(
                NextPointProgress(
                    category="clue",
                    name=clue.name,
                    display_name=clue.display_name,
                    current=clue.kc,
                    emoji_key=clue.emoji_key,
                    points=clue.points,
                    progress_percent=1 - (raw_remaining / bucket),
                    remaining_to_next=remaining,
                    unit="kc",
                    time_hours=time_hours,
                )
            )

        results.sort(key=lambda e: (e.time_hours is None, e.time_hours, e.name))
        return results[:limit]

    async def get_player_points_total(
        self, player_name: str, bypass_cache: bool | None = False
    ) -> int:
        normalized_name: str = normalize_discord_string(input=player_name)
        data: ScoreBreakdown = await self.get_player_score(
            normalized_name, bypass_cache
        )

        activities: list[ActivityScore] = data.clues + data.raids + data.bosses

        points = 0
        for skill in data.skills:
            points += skill.points

        for activity in activities:
            points += activity.points

        return points

    async def get_rank(self, player_name: str) -> RANK:
        try:
            total_points: int = await self.get_player_points_total(player_name)
        except RuntimeError as e:
            raise e

        return RANK(value=get_rank_from_points(points=total_points))


def get_score_service(http: AsyncHttpClient = None) -> ScoreService:
    """Get a singleton ScoreService instance to avoid unnecessary recreation."""
    global _score_service_instance

    if _score_service_instance is None and http is not None:
        _score_service_instance = ScoreService(http)

    if _score_service_instance is None:
        raise RuntimeError(
            "ScoreService not initialized. Call with http parameter first."
        )

    return _score_service_instance
