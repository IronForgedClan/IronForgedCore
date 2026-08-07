import unittest
from unittest.mock import AsyncMock, patch

from ironforgedcore.services.score_service import ScoreService
from ironforgedcore.exceptions.score_exceptions import HiscoresError, HiscoresNotFound
from ironforgedcore.models.score import (
    ActivityScore,
    NextPointProgress,
    ScoreBreakdown,
    SkillScore,
)
from ironforgedcore.common.ranks import RANK
from ironforgedcore.storage import data as data_module


class TestScoreService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_http = AsyncMock()
        self.score_service = ScoreService(self.mock_http)

        self.sample_skills_data = [
            {"id": 0, "name": "Overall", "rank": 73537, "level": 2269, "xp": 431062657},
            {"id": 1, "name": "Attack", "rank": 230259, "level": 99, "xp": 14871752},
            {"id": 2, "name": "Defence", "rank": 280185, "level": 99, "xp": 13415365},
            {"id": 17, "name": "Agility", "rank": 126508, "level": 95, "xp": 9243572},
        ]

        self.sample_activities_data = [
            {"id": 71, "name": "Theatre of Blood", "rank": -1, "score": -1},
            {"id": 29, "name": "Chambers of Xeric", "rank": -1, "score": -1},
            {"id": 85, "name": "Zulrah", "rank": 331152, "score": 175},
            {"id": 6, "name": "Clue Scrolls (all)", "rank": 4743, "score": 3570},
            {"id": 19, "name": "Abyssal Sire", "rank": 43106, "score": 747},
        ]

        self.sample_response_data = {
            "skills": self.sample_skills_data,
            "activities": self.sample_activities_data,
        }

        self.sample_skills_config = [
            {
                "name": "Attack",
                "display_order": 1,
                "emoji_key": "Attack",
                "xp_per_point": 100000,
                "xp_per_point_post_99": 300000,
            },
            {
                "name": "Defence",
                "display_order": 7,
                "emoji_key": "Defence",
                "xp_per_point": 100000,
                "xp_per_point_post_99": 300000,
            },
            {
                "name": "Agility",
                "display_order": 5,
                "emoji_key": "Agility",
                "xp_per_point": 30000,
                "xp_per_point_post_99": 90000,
            },
        ]

        self.sample_raids_config = [
            {
                "name": "Theatre of Blood",
                "display_order": 3,
                "emoji_key": "Theatre_of_Blood",
                "kc_per_point": 0.4,
            },
            {
                "name": "Chambers of Xeric",
                "display_order": 1,
                "emoji_key": "Chambers_of_Xeric",
                "kc_per_point": 0.8,
            },
        ]

        self.sample_bosses_config = [
            {
                "name": "Zulrah",
                "display_order": 59,
                "emoji_key": "Zulrah",
                "kc_per_point": 12,
            },
            {
                "name": "Abyssal Sire",
                "display_order": 2,
                "emoji_key": "Abyssal_Sire",
                "kc_per_point": 10,
            },
        ]

        self.sample_clues_config = [
            {
                "name": "Clue Scrolls (beginner)",
                "display_name": "Beginner",
                "display_order": 1,
                "emoji_key": "Beginner_Clue",
                "kc_per_point": 10,
            },
            {
                "name": "Clue Scrolls (easy)",
                "display_name": "Easy",
                "display_order": 2,
                "emoji_key": "Easy_Clue",
                "kc_per_point": 5,
            },
        ]

        data_module.set_data(
            skills=self.sample_skills_config,
            clues=self.sample_clues_config,
            raids=self.sample_raids_config,
            bosses=self.sample_bosses_config,
        )

    def test_init(self):
        """Test ScoreService initialization"""
        self.assertEqual(self.score_service.http, self.mock_http)
        self.assertIn("hiscore_oldschool", self.score_service.hiscores_url)
        self.assertEqual(self.score_service.level_99_xp, 13_034_431)

    @patch("ironforgedcore.services.score_service.SCORE_CACHE")
    @patch("ironforgedcore.services.score_service.normalize_discord_string")
    async def test_get_player_score_cache_hit(self, mock_normalize, mock_cache):
        """Test get_player_score returns cached data when available"""
        player_name = "TestPlayer"
        mock_normalize.return_value = player_name

        mock_breakdown = ScoreBreakdown(skills=[], clues=[], raids=[], bosses=[])
        mock_cache.get = AsyncMock(return_value=mock_breakdown)

        result = await self.score_service.get_player_score(player_name)

        self.assertEqual(result, mock_breakdown)
        mock_cache.get.assert_called_once_with(player_name)
        self.mock_http.get.assert_not_called()

    @patch("ironforgedcore.services.score_service.SCORE_CACHE")
    @patch("ironforgedcore.services.score_service.normalize_discord_string")
    async def test_get_player_score_cache_miss_with_valid_response(
        self, mock_normalize, mock_cache
    ):
        """Test get_player_score fetches and caches data when cache miss"""
        player_name = "TestPlayer"
        mock_normalize.return_value = player_name
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        self.mock_http.get.return_value = {
            "status": 200,
            "body": self.sample_response_data,
        }

        result = await self.score_service.get_player_score(player_name)

        self.assertIsInstance(result, ScoreBreakdown)
        self.assertIsInstance(result.skills, list)
        self.assertIsInstance(result.clues, list)
        self.assertIsInstance(result.raids, list)
        self.assertIsInstance(result.bosses, list)
        mock_cache.set.assert_called_once()
        self.mock_http.get.assert_called_once()

    @patch("ironforgedcore.services.score_service.SCORE_CACHE")
    @patch("ironforgedcore.services.score_service.normalize_discord_string")
    async def test_get_player_score_404_error(self, mock_normalize, mock_cache):
        """Test get_player_score raises HiscoresNotFound for 404 response"""
        player_name = "NonExistentPlayer"
        mock_normalize.return_value = player_name
        mock_cache.get = AsyncMock(return_value=None)

        self.mock_http.get.return_value = {"status": 404}

        with self.assertRaises(HiscoresNotFound):
            await self.score_service.get_player_score(player_name)

    @patch("ironforgedcore.services.score_service.SCORE_CACHE")
    @patch("ironforgedcore.services.score_service.normalize_discord_string")
    async def test_get_player_score_server_error(self, mock_normalize, mock_cache):
        """Test get_player_score raises HiscoresError for server errors"""
        player_name = "TestPlayer"
        mock_normalize.return_value = player_name
        mock_cache.get = AsyncMock(return_value=None)

        self.mock_http.get.return_value = {"status": 500}

        with self.assertRaises(HiscoresError) as context:
            await self.score_service.get_player_score(player_name)

        self.assertIn("Unexpected response code 500", str(context.exception))

    @patch("ironforgedcore.services.score_service.SCORE_CACHE")
    @patch("ironforgedcore.services.score_service.normalize_discord_string")
    async def test_get_player_score_bypass_cache(self, mock_normalize, mock_cache):
        """Test get_player_score bypasses cache when bypass_cache=True"""
        player_name = "TestPlayer"
        mock_normalize.return_value = player_name
        mock_breakdown = ScoreBreakdown(skills=[], clues=[], raids=[], bosses=[])
        mock_cache.get = AsyncMock(return_value=mock_breakdown)
        mock_cache.set = AsyncMock()

        self.mock_http.get.return_value = {
            "status": 200,
            "body": {"skills": [], "activities": []},
        }

        result = await self.score_service.get_player_score(
            player_name, bypass_cache=True
        )

        self.mock_http.get.assert_called_once()
        mock_cache.set.assert_called_once()

    def test_process_skills_no_skills_data(self):
        """Test _process_skills raises RuntimeError when SKILLS is None"""
        with patch("ironforgedcore.storage.data.SKILLS", None):
            with self.assertRaises(RuntimeError) as context:
                self.score_service._process_skills(self.sample_response_data)

            self.assertEqual(str(context.exception), "Unable to read skills data")

    def test_process_skills_none_score_data(self):
        """Test _process_skills raises RuntimeError when score_data is None"""
        with self.assertRaises(RuntimeError):
            self.score_service._process_skills(None)

    def test_process_skills_none_skills_in_data(self):
        """Test _process_skills raises RuntimeError when skills key is None"""
        with self.assertRaises(RuntimeError):
            self.score_service._process_skills({"skills": None})

    def test_process_skills_valid_data(self):
        """Test _process_skills with valid skill data"""
        result = self.score_service._process_skills(self.sample_response_data)

        self.assertIsInstance(result, list)
        skill_names = [skill.name for skill in result]
        self.assertNotIn("Overall", skill_names)

    def test_process_skills_skips_overall(self):
        """Test _process_skills skips Overall skill"""
        result = self.score_service._process_skills(self.sample_response_data)

        skill_names = [skill.name for skill in result]
        self.assertNotIn("Overall", skill_names)

    def test_process_skills_handles_missing_skill(self):
        """Test _process_skills handles skills not in SKILLS config"""
        data_module.set_data(skills=[])

        test_data = {
            "skills": [
                {
                    "id": 0,
                    "name": "Overall",
                    "rank": 73537,
                    "level": 2269,
                    "xp": 431062657,
                },
                {
                    "id": 999,
                    "name": "NonexistentSkill",
                    "rank": 1,
                    "level": 50,
                    "xp": 100000,
                },
            ]
        }

        result = self.score_service._process_skills(test_data)

        self.assertEqual(result, [])

    def test_process_skills_level_below_99(self):
        """Test _process_skills calculates points correctly for level < 99"""
        test_data = {
            "skills": [
                {"id": 2, "name": "Defence", "rank": 280185, "level": 85, "xp": 3500000}
            ]
        }

        result = self.score_service._process_skills(test_data)

        self.assertEqual(len(result), 1)
        skill = result[0]
        self.assertEqual(skill.name, "Defence")
        self.assertEqual(skill.level, 85)
        self.assertEqual(skill.xp, 3500000)
        self.assertEqual(skill.points, 35)

    def test_process_skills_level_99_plus(self):
        """Test _process_skills calculates points correctly for level >= 99"""
        test_data = {
            "skills": [
                {"id": 1, "name": "Attack", "rank": 230259, "level": 99, "xp": 15000000}
            ]
        }

        result = self.score_service._process_skills(test_data)

        self.assertEqual(len(result), 1)
        skill = result[0]
        self.assertEqual(skill.name, "Attack")
        self.assertEqual(skill.level, 99)
        self.assertEqual(skill.xp, 15000000)

        expected_points = int(13034431 / 100000) + int((15000000 - 13034431) / 300000)
        self.assertEqual(skill.points, expected_points)

    def test_process_skills_minimum_level_and_xp(self):
        """Test _process_skills handles minimum level and XP values"""
        test_data = {
            "skills": [{"id": 1, "name": "Attack", "rank": 1, "level": 0, "xp": -100}]
        }

        result = self.score_service._process_skills(test_data)

        self.assertEqual(len(result), 1)
        skill = result[0]
        self.assertEqual(skill.level, 1)
        self.assertEqual(skill.xp, 0)
        self.assertEqual(skill.points, 0)

    def test_process_skills_creates_correct_skillscore_objects(self):
        """Test _process_skills creates SkillScore objects with correct attributes"""
        test_data = {
            "skills": [
                {"id": 1, "name": "Attack", "rank": 230259, "level": 70, "xp": 800000}
            ]
        }

        result = self.score_service._process_skills(test_data)

        self.assertEqual(len(result), 1)
        skill = result[0]

        self.assertIsInstance(skill, SkillScore)
        self.assertEqual(skill.name, "Attack")
        self.assertEqual(skill.display_name, None)
        self.assertEqual(skill.display_order, 1)
        self.assertEqual(skill.emoji_key, "Attack")
        self.assertEqual(skill.level, 70)
        self.assertEqual(skill.xp, 800000)
        self.assertEqual(skill.points, 8)

    def test_process_activities_no_activity_data(self):
        """Test _process_activities raises RuntimeError when activity data is None"""
        with (
            patch("ironforgedcore.storage.data.CLUES", None),
            patch("ironforgedcore.storage.data.BOSSES", None),
            patch("ironforgedcore.storage.data.RAIDS", None),
        ):
            with self.assertRaises(RuntimeError) as context:
                self.score_service._process_activities(self.sample_response_data)

            self.assertEqual(str(context.exception), "Unable to read activity data")

    def test_process_activities_valid_data(self):
        """Test _process_activities with valid activity data"""
        clues, raids, bosses = self.score_service._process_activities(
            self.sample_response_data
        )

        self.assertIsInstance(clues, list)
        self.assertIsInstance(raids, list)
        self.assertIsInstance(bosses, list)

    def test_process_activities_boss_zero_kc_filtered(self):
        """Test _process_activities filters out bosses with 0 KC"""
        data_module.set_data(clues=[], raids=[], bosses=self.sample_bosses_config)

        test_data = {
            "activities": [
                {
                    "id": 85,
                    "name": "Zulrah",
                    "rank": -1,
                    "score": 0,
                }
            ]
        }

        clues, raids, bosses = self.score_service._process_activities(test_data)

        self.assertEqual(len(bosses), 0)

    def test_process_activities_negative_kc_becomes_zero(self):
        """Test _process_activities handles negative KC by making it 0"""
        data_module.set_data(clues=self.sample_clues_config, raids=[], bosses=[])

        test_data = {
            "activities": [
                {
                    "id": 7,
                    "name": "Clue Scrolls (beginner)",
                    "rank": 253,
                    "score": -50,
                }
            ]
        }

        clues, raids, bosses = self.score_service._process_activities(test_data)

        self.assertEqual(len(clues), 1)
        self.assertEqual(clues[0].kc, 0)
        self.assertEqual(clues[0].points, 0)

    def test_process_activities_display_name_handling(self):
        """Test _process_activities handles display_name correctly"""
        data_module.set_data(clues=[], raids=self.sample_raids_config, bosses=[])

        test_data = {
            "activities": [
                {"id": 71, "name": "Theatre of Blood", "rank": -1, "score": 150}
            ]
        }

        clues, raids, bosses = self.score_service._process_activities(test_data)

        self.assertEqual(len(raids), 1)
        self.assertEqual(raids[0].display_name, None)

    def test_process_activities_creates_correct_activityscore_objects(self):
        """Test _process_activities creates ActivityScore objects with correct attributes"""
        data_module.set_data(clues=self.sample_clues_config, raids=[], bosses=[])

        test_data = {
            "activities": [
                {"id": 7, "name": "Clue Scrolls (beginner)", "rank": 253, "score": 1000}
            ]
        }

        clues, raids, bosses = self.score_service._process_activities(test_data)

        self.assertEqual(len(clues), 1)
        clue = clues[0]

        self.assertIsInstance(clue, ActivityScore)
        self.assertEqual(clue.name, "Clue Scrolls (beginner)")
        self.assertEqual(clue.display_name, "Beginner")
        self.assertEqual(clue.display_order, 1)
        self.assertEqual(clue.emoji_key, "Beginner_Clue")
        self.assertEqual(clue.kc, 1000)
        self.assertEqual(clue.points, 100)

    @patch("ironforgedcore.services.score_service.normalize_discord_string")
    async def test_get_player_points_total(self, mock_normalize):
        """Test get_player_points_total calculates total correctly"""
        player_name = "TestPlayer"
        mock_normalize.return_value = player_name

        skill1 = SkillScore(
            name="Attack",
            display_name=None,
            display_order=1,
            emoji_key="attack",
            xp=1000000,
            level=80,
            points=100,
        )
        skill2 = SkillScore(
            name="Defence",
            display_name=None,
            display_order=2,
            emoji_key="defence",
            xp=2000000,
            level=90,
            points=200,
        )

        activity1 = ActivityScore(
            name="Zulrah",
            display_name=None,
            display_order=1,
            emoji_key="zulrah",
            kc=100,
            points=50,
        )
        activity2 = ActivityScore(
            name="CoX",
            display_name=None,
            display_order=2,
            emoji_key="cox",
            kc=150,
            points=75,
        )

        mock_breakdown = ScoreBreakdown(
            skills=[skill1, skill2], clues=[activity1], raids=[activity2], bosses=[]
        )

        with patch.object(
            self.score_service, "get_player_score", return_value=mock_breakdown
        ):
            result = await self.score_service.get_player_points_total(player_name)

            self.assertEqual(result, 425)

    @patch("ironforgedcore.services.score_service.get_rank_from_points")
    async def test_get_rank(self, mock_get_rank_from_points):
        """Test get_rank returns correct rank based on points"""
        player_name = "TestPlayer"
        mock_get_rank_from_points.return_value = "Dragon"

        with patch.object(
            self.score_service, "get_player_points_total", return_value=5000
        ) as mock_points:
            result = await self.score_service.get_rank(player_name)

            self.assertIsInstance(result, RANK)
            self.assertEqual(result.value, "Dragon")
            mock_points.assert_called_once_with(player_name)
            mock_get_rank_from_points.assert_called_once_with(points=5000)

    async def test_get_rank_runtime_error(self):
        """Test get_rank propagates RuntimeError from get_player_points_total"""
        player_name = "TestPlayer"

        with patch.object(
            self.score_service,
            "get_player_points_total",
            side_effect=RuntimeError("Test error"),
        ):
            with self.assertRaises(RuntimeError):
                await self.score_service.get_rank(player_name)

    def test_hiscores_url_format(self):
        """Test that hiscores URL is correctly formatted"""
        expected_url = (
            "https://secure.runescape.com/m=hiscore_oldschool/"
            "index_lite.json?player={rsn}"
        )
        self.assertEqual(self.score_service.hiscores_url, expected_url)

    def test_process_skills_with_string_level_and_xp(self):
        """Test _process_skills handles string values for level and XP"""
        test_data = {
            "skills": [
                {
                    "id": 1,
                    "name": "Attack",
                    "rank": 230259,
                    "level": "70",
                    "xp": "800000",
                }
            ]
        }

        result = self.score_service._process_skills(test_data)

        self.assertEqual(len(result), 1)
        skill = result[0]
        self.assertEqual(skill.level, 70)
        self.assertEqual(skill.xp, 800000)

    def test_process_activities_with_string_score(self):
        """Test _process_activities handles string values for score"""
        data_module.set_data(clues=self.sample_clues_config, raids=[], bosses=[])

        test_data = {
            "activities": [
                {
                    "id": 7,
                    "name": "Clue Scrolls (beginner)",
                    "rank": 253,
                    "score": "1000",
                }
            ]
        }

        clues, raids, bosses = self.score_service._process_activities(test_data)

        self.assertEqual(len(clues), 1)
        self.assertEqual(clues[0].kc, 1000)

    def test_process_activities_handles_negative_one_scores(self):
        """Test _process_activities handles -1 scores (unattempted activities)"""
        data_module.set_data(clues=[], raids=self.sample_raids_config, bosses=[])

        test_data = {
            "activities": [
                {
                    "id": 71,
                    "name": "Theatre of Blood",
                    "rank": -1,
                    "score": -1,
                }
            ]
        }

        clues, raids, bosses = self.score_service._process_activities(test_data)

        self.assertEqual(len(raids), 1)
        self.assertEqual(raids[0].kc, 0)
        self.assertEqual(raids[0].points, 0)

    def test_process_skills_with_very_high_xp(self):
        """Test _process_skills handles very high XP values correctly"""
        test_data = {
            "skills": [
                {
                    "id": 1,
                    "name": "Attack",
                    "rank": 230259,
                    "level": 99,
                    "xp": 25000000,
                }
            ]
        }

        result = self.score_service._process_skills(test_data)

        self.assertEqual(len(result), 1)
        skill = result[0]
        self.assertEqual(skill.name, "Attack")
        self.assertEqual(skill.level, 99)
        self.assertEqual(skill.xp, 25000000)

        expected_points = int(13034431 / 100000) + int((25000000 - 13034431) / 300000)
        self.assertEqual(skill.points, expected_points)

    def test_process_activities_with_realistic_high_scores(self):
        """Test _process_activities with realistic high activity scores"""
        data_module.set_data(clues=self.sample_clues_config, raids=[], bosses=[])

        test_data = {
            "activities": [
                {
                    "id": 7,
                    "name": "Clue Scrolls (beginner)",
                    "rank": 253,
                    "score": 3570,
                }
            ]
        }

        clues, raids, bosses = self.score_service._process_activities(test_data)

        self.assertEqual(len(clues), 1)
        clue = clues[0]
        self.assertEqual(clue.kc, 3570)
        self.assertEqual(clue.points, 357)

    def test_process_activities_handles_negative_one_api_values(self):
        """Test _process_activities handles -1 values from API (unattempted activities)"""
        data_module.set_data(clues=[], raids=self.sample_raids_config, bosses=[])

        test_data = {
            "activities": [
                {
                    "id": 71,
                    "name": "Theatre of Blood",
                    "rank": -1,
                    "score": -1,
                }
            ]
        }

        clues, raids, bosses = self.score_service._process_activities(test_data)

        self.assertEqual(len(raids), 1)
        raid = raids[0]
        self.assertEqual(raid.kc, 0)
        self.assertEqual(raid.points, 0)

    def test_process_activities_with_float_kc_per_point(self):
        """Test _process_activities handles float kc_per_point values correctly"""
        data_module.set_data(clues=[], raids=self.sample_raids_config, bosses=[])

        test_data = {
            "activities": [
                {"id": 71, "name": "Theatre of Blood", "rank": 1000, "score": 150}
            ]
        }

        clues, raids, bosses = self.score_service._process_activities(test_data)

        self.assertEqual(len(raids), 1)
        raid = raids[0]
        self.assertEqual(raid.kc, 150)
        self.assertEqual(raid.points, 375)


class TestGetProximityToNextPoint(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_http = AsyncMock()
        self.score_service = ScoreService(self.mock_http)

        self.skills_config = [
            {
                "name": "Attack",
                "display_order": 1,
                "emoji_key": "Attack",
                "xp_per_point": 100000,
                "xp_per_point_post_99": 300000,
            },
            {
                "name": "Defence",
                "display_order": 7,
                "emoji_key": "Defence",
                "xp_per_point": 100000,
                "xp_per_point_post_99": 300000,
            },
            {
                "name": "Agility",
                "display_order": 5,
                "emoji_key": "Agility",
                "xp_per_point": 30000,
                "xp_per_point_post_99": 90000,
            },
        ]
        self.bosses_config = [
            {
                "name": "Zulrah",
                "display_order": 59,
                "emoji_key": "Zulrah",
                "kc_per_point": 12,
            },
            {
                "name": "Abyssal Sire",
                "display_order": 2,
                "emoji_key": "Abyssal_Sire",
                "kc_per_point": 10,
            },
        ]
        self.raids_config = [
            {
                "name": "Chambers of Xeric",
                "display_order": 1,
                "emoji_key": "Chambers_of_Xeric",
                "kc_per_point": 0.8,
            },
        ]
        self.clues_config = [
            {
                "name": "Clue Scrolls (beginner)",
                "display_name": "Beginner",
                "display_order": 1,
                "emoji_key": "Beginner_Clue",
                "kc_per_point": 10,
            },
        ]

        data_module.set_data(
            skills=self.skills_config,
            bosses=self.bosses_config,
            raids=self.raids_config,
            clues=self.clues_config,
        )

    async def test_empty_breakdown_returns_empty_list(self):
        breakdown = ScoreBreakdown(skills=[], clues=[], raids=[], bosses=[])

        result = await self.score_service.get_proximity_to_next_point(breakdown)

        self.assertEqual(result, [])

    async def test_skill_below_99_returns_correct_progress(self):
        skill = SkillScore("Attack", None, 1, "Attack", 80000, 70, 0)
        breakdown = ScoreBreakdown(skills=[skill], clues=[], raids=[], bosses=[])

        result = await self.score_service.get_proximity_to_next_point(breakdown)

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry.category, "skill")
        self.assertEqual(entry.name, "Attack")
        self.assertEqual(entry.emoji_key, "Attack")
        self.assertEqual(entry.points, 0)
        self.assertEqual(entry.unit, "xp")
        self.assertEqual(entry.remaining_to_next, 20000)
        self.assertAlmostEqual(entry.progress_percent, 0.8)

    async def test_skill_at_point_threshold_is_zero_percent(self):
        skill = SkillScore("Attack", None, 1, "Attack", 200000, 99, 2)
        breakdown = ScoreBreakdown(skills=[skill], clues=[], raids=[], bosses=[])

        result = await self.score_service.get_proximity_to_next_point(breakdown)

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry.points, 2)
        self.assertEqual(entry.remaining_to_next, 100000)
        self.assertAlmostEqual(entry.progress_percent, 0.0)

    async def test_skill_post_99_uses_post_99_bucket(self):
        skill = SkillScore("Attack", None, 1, "Attack", 13200000, 99, 130)
        breakdown = ScoreBreakdown(skills=[skill], clues=[], raids=[], bosses=[])

        result = await self.score_service.get_proximity_to_next_point(breakdown)

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry.points, 130)
        self.assertEqual(entry.unit, "xp")
        self.assertEqual(entry.remaining_to_next, 134431)
        self.assertAlmostEqual(entry.progress_percent, 1 - 134431 / 300000, places=5)

    async def test_skill_zero_xp_excluded(self):
        skill = SkillScore("Attack", None, 1, "Attack", 0, 1, 0)
        breakdown = ScoreBreakdown(skills=[skill], clues=[], raids=[], bosses=[])

        result = await self.score_service.get_proximity_to_next_point(breakdown)

        self.assertEqual(result, [])

    async def test_boss_returns_correct_progress(self):
        boss = ActivityScore("Zulrah", None, 59, "Zulrah", 11, 0)
        breakdown = ScoreBreakdown(skills=[], clues=[], raids=[], bosses=[boss])

        result = await self.score_service.get_proximity_to_next_point(breakdown)

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry.category, "boss")
        self.assertEqual(entry.name, "Zulrah")
        self.assertEqual(entry.unit, "kc")
        self.assertEqual(entry.remaining_to_next, 1)
        self.assertAlmostEqual(entry.progress_percent, 11 / 12)

    async def test_raid_with_float_kc_per_point(self):
        raid = ActivityScore("Chambers of Xeric", None, 1, "Chambers_of_Xeric", 10, 12)
        breakdown = ScoreBreakdown(skills=[], clues=[], raids=[raid], bosses=[])

        result = await self.score_service.get_proximity_to_next_point(breakdown)

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry.category, "raid")
        self.assertEqual(entry.unit, "kc")
        self.assertAlmostEqual(entry.remaining_to_next, 0.4, places=5)
        self.assertAlmostEqual(entry.progress_percent, 0.5)

    async def test_clue_preserves_display_name(self):
        clue = ActivityScore(
            "Clue Scrolls (beginner)", "Beginner", 1, "Beginner_Clue", 5, 0
        )
        breakdown = ScoreBreakdown(skills=[], clues=[clue], raids=[], bosses=[])

        result = await self.score_service.get_proximity_to_next_point(breakdown)

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry.category, "clue")
        self.assertEqual(entry.display_name, "Beginner")
        self.assertEqual(entry.remaining_to_next, 5)
        self.assertAlmostEqual(entry.progress_percent, 0.5)

    async def test_activity_zero_kc_excluded(self):
        boss = ActivityScore("Zulrah", None, 59, "Zulrah", 0, 0)
        breakdown = ScoreBreakdown(skills=[], clues=[], raids=[], bosses=[boss])

        result = await self.score_service.get_proximity_to_next_point(breakdown)

        self.assertEqual(result, [])

    async def test_results_sorted_by_pct_desc(self):
        skills = [
            SkillScore("Attack", None, 1, "Attack", 20000, 20, 0),
            SkillScore("Defence", None, 7, "Defence", 90000, 90, 0),
        ]
        bosses = [ActivityScore("Zulrah", None, 59, "Zulrah", 1, 0)]
        clues = [
            ActivityScore(
                "Clue Scrolls (beginner)", "Beginner", 1, "Beginner_Clue", 9, 0
            )
        ]
        breakdown = ScoreBreakdown(skills=skills, clues=clues, raids=[], bosses=bosses)

        result = await self.score_service.get_proximity_to_next_point(breakdown)

        self.assertEqual(len(result), 4)
        pcts = [e.progress_percent for e in result]
        self.assertEqual(pcts, sorted(pcts, reverse=True))

    async def test_ties_broken_by_name_ascending(self):
        skills = [
            SkillScore("Defence", None, 7, "Defence", 50000, 50, 0),
            SkillScore("Attack", None, 1, "Attack", 50000, 50, 0),
        ]
        breakdown = ScoreBreakdown(skills=skills, clues=[], raids=[], bosses=[])

        result = await self.score_service.get_proximity_to_next_point(breakdown)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "Attack")
        self.assertEqual(result[1].name, "Defence")

    async def test_capped_at_ten_results(self):
        skills = [
            SkillScore(f"Skill{i}", None, i, f"Skill{i}", (i + 1) * 1000, 10, 0)
            for i in range(12)
        ]
        data_module.set_data(
            skills=[
                {
                    "name": f"Skill{i}",
                    "display_order": i,
                    "emoji_key": f"Skill{i}",
                    "xp_per_point": 1000,
                    "xp_per_point_post_99": 3000,
                }
                for i in range(12)
            ],
            bosses=[],
            raids=[],
            clues=[],
        )
        breakdown = ScoreBreakdown(skills=skills, clues=[], raids=[], bosses=[])

        result = await self.score_service.get_proximity_to_next_point(breakdown)

        self.assertEqual(len(result), 10)

    async def test_returns_nextpointprogress_instances(self):
        skill = SkillScore("Attack", None, 1, "Attack", 50000, 50, 0)
        breakdown = ScoreBreakdown(skills=[skill], clues=[], raids=[], bosses=[])

        result = await self.score_service.get_proximity_to_next_point(breakdown)

        self.assertIsInstance(result[0], NextPointProgress)
