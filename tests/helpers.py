import itertools
from typing import Any, List, Optional
from unittest.mock import AsyncMock, Mock

from sqlalchemy.ext.asyncio import AsyncSession

_id_counter = itertools.count(100000)


def create_mock_db_session() -> AsyncMock:
    """Build a mock AsyncSession with the correct sync/async method split.

    AsyncMock(spec=AsyncSession) makes sync session methods (add, merge,
    expire, ...) return sync MagicMock, and async methods (commit,
    execute, flush, refresh, delete, rollback, ...) return AsyncMock.
    Use this anywhere a test needs to mock a database session.
    """
    return AsyncMock(spec=AsyncSession)


def setup_database_service_mocks(
    mock_db, mock_service_factory, mock_service_instance=None
):
    """Sets up common database and service mocking pattern used across many tests.

    Args:
        mock_db: Mock of the database module
        mock_service_factory: Mock of the service factory function (e.g., create_ingot_service)
        mock_service_instance: Optional mock service instance to return
    """
    mock_session = create_mock_db_session()

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_session
    mock_context_manager.__aexit__.return_value = None
    mock_db.get_session.return_value = mock_context_manager

    if mock_service_instance is None:
        mock_service_instance = AsyncMock()

    mock_service_factory.return_value = mock_service_instance

    return mock_session, mock_service_instance


def create_test_db_member(
    nickname="TestUser",
    discord_id=None,
    rank="Iron",
    ingots=1000,
    active=True,
    joined_date=None,
    is_booster=False,
    is_prospect=False,
    is_blacklisted=False,
    is_banned=False,
    **kwargs,
):
    """Creates test Member model instance with common defaults."""
    from datetime import datetime, timezone

    member = Mock()
    if "id" in kwargs:
        member.id = kwargs.pop("id")
    else:
        member.id = f"test-member-{next(_id_counter)}"

    member.nickname = nickname
    member.discord_id = discord_id or next(_id_counter)
    member.rank = rank
    member.ingots = ingots
    member.active = active
    member.joined_date = joined_date or datetime.now(timezone.utc)
    member.is_booster = is_booster
    member.is_prospect = is_prospect
    member.is_blacklisted = is_blacklisted
    member.is_banned = is_banned

    for key, value in kwargs.items():
        setattr(member, key, value)

    return member


def setup_time_mocks(
    mock_datetime, mock_time, fixed_datetime=None, duration_seconds=5.0
):
    """Sets up standard time mocking pattern for consistent testing."""
    from datetime import datetime, timezone

    if fixed_datetime is None:
        fixed_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    if mock_datetime:
        mock_datetime.now.return_value = fixed_datetime
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

    if mock_time:
        mock_time.perf_counter.side_effect = [0.0, duration_seconds]

    return fixed_datetime


def create_test_score_breakdown(skills_count=2, activities_count=2):
    """Creates real ScoreBreakdown object for cache serialization testing."""
    from ironforgedcore.models.score import ScoreBreakdown, SkillScore, ActivityScore

    skills = []
    for i in range(skills_count):
        skill = SkillScore(
            name=f"Skill{i+1}",
            display_name=f"Skill {i+1}",
            display_order=i + 1,
            emoji_key=f"skill_{i+1}",
            xp=13034000 - (i * 1000000),
            level=99 - (i * 5),
            points=1000 - (i * 100),
        )
        skills.append(skill)

    clues = []
    raids = []
    bosses = []

    for i in range(min(activities_count, 1)):
        clue = ActivityScore(
            name=f"Clue{i+1}",
            display_name=f"Clue {i+1}",
            display_order=i + 1,
            emoji_key=f"clue_{i+1}",
            kc=200 - (i * 50),
            points=100 - (i * 25),
        )
        clues.append(clue)

    for i in range(min(activities_count, 1)):
        raid = ActivityScore(
            name=f"Raid{i+1}",
            display_name=f"Raid {i+1}",
            display_order=i + 1,
            emoji_key=f"raid_{i+1}",
            kc=150 - (i * 30),
            points=75 - (i * 15),
        )
        raids.append(raid)

    for i in range(max(0, activities_count - 2)):
        boss = ActivityScore(
            name=f"Boss{i+1}",
            display_name=f"Boss {i+1}",
            display_order=i + 1,
            emoji_key=f"boss_{i+1}",
            kc=100 - (i * 20),
            points=50 - (i * 10),
        )
        bosses.append(boss)

    return ScoreBreakdown(skills=skills, clues=clues, raids=raids, bosses=bosses)


def validate_role_mappings() -> list[str]:
    """
    Validate the role mapping configuration for consistency.

    Returns:
        List of validation error messages (empty if valid)
    """
    from ironforgedcore.common.ranks import RANK
    from ironforgedcore.common.roles import ROLE
    from ironforgedcore.common.wom_role_mapping import (
        WOM_TO_DISCORD_RANK_MAPPING,
        WOM_TO_DISCORD_ROLE_MAPPING,
    )
    from ironforgedcore.common.ranks import get_activity_threshold_for_rank

    errors = []

    mapped_discord_ranks = set(WOM_TO_DISCORD_RANK_MAPPING.values())
    valid_ranks = set(RANK)

    invalid_ranks = mapped_discord_ranks - valid_ranks
    if invalid_ranks:
        errors.append(f"Invalid ranks in mapping: {invalid_ranks}")

    mapped_discord_roles = set(WOM_TO_DISCORD_ROLE_MAPPING.values())
    valid_roles = set(ROLE)

    invalid_roles = mapped_discord_roles - valid_roles
    if invalid_roles:
        errors.append(f"Invalid roles in mapping: {invalid_roles}")

    for rank in mapped_discord_ranks:
        try:
            threshold = get_activity_threshold_for_rank(rank)
            if threshold < 0:
                errors.append(f"Negative threshold for rank {rank}: {threshold}")
        except Exception as e:
            errors.append(f"Error getting threshold for rank {rank}: {e}")

    return errors


def get_all_wom_roles_for_discord_role(discord_role) -> list:
    """
    Get all WOM roles that map to a specific Discord role.

    Args:
        discord_role: Discord ROLE enum value

    Returns:
        List of WOM GroupRole values that map to the Discord role
    """
    from wom import GroupRole
    from ironforgedcore.common.wom_role_mapping import WOM_TO_DISCORD_ROLE_MAPPING

    return [
        wom_role
        for wom_role, mapped_role in WOM_TO_DISCORD_ROLE_MAPPING.items()
        if mapped_role == discord_role
    ]


def get_all_wom_roles_for_discord_rank(discord_rank) -> list:
    """
    Get all WOM roles that map to a specific Discord rank.

    Args:
        discord_rank: Discord RANK enum value

    Returns:
        List of WOM GroupRole values that map to the Discord rank
    """
    from wom import GroupRole
    from ironforgedcore.common.wom_role_mapping import WOM_TO_DISCORD_RANK_MAPPING

    return [
        wom_role
        for wom_role, mapped_rank in WOM_TO_DISCORD_RANK_MAPPING.items()
        if mapped_rank == discord_rank
    ]
