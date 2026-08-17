import unittest

from ironforgedcore.common.time import format_duration_hours


class TestFormatDurationHours(unittest.TestCase):
    def test_none_returns_dash(self):
        self.assertEqual(format_duration_hours(None, "ehp"), "—")

    def test_zero_hours_returns_dash(self):
        self.assertEqual(format_duration_hours(0, "ehp"), "~0min ehp")

    def test_sub_minute_rounds_up_to_one_minute(self):
        self.assertEqual(format_duration_hours(0.001, "ehp"), "~1min ehp")

    def test_under_one_minute_uses_minute_bucket(self):
        self.assertEqual(format_duration_hours(0.5 / 60, "ehp"), "~1min ehp")

    def test_minutes_only(self):
        self.assertEqual(format_duration_hours(5 / 60, "ehp"), "~5min ehp")

    def test_minutes_only_with_ehb_suffix(self):
        self.assertEqual(format_duration_hours(45 / 60, "ehb"), "~45min ehb")

    def test_exactly_one_hour_no_minutes(self):
        self.assertEqual(format_duration_hours(1.0, "ehp"), "~1hr ehp")

    def test_hours_and_minutes(self):
        self.assertEqual(format_duration_hours(1.0 + 5 / 60, "ehp"), "~1hr 5min ehp")

    def test_multiple_hours(self):
        self.assertEqual(format_duration_hours(3.5, "ehp"), "~3hr 30min ehp")

    def test_hours_minutes_rounding(self):
        self.assertEqual(format_duration_hours(2.25, "ehp"), "~2hr 15min ehp")

    def test_minutes_rounding_to_next_hour(self):
        self.assertEqual(format_duration_hours(2.999, "ehp"), "~3hr ehp")

    def test_just_under_one_day(self):
        self.assertEqual(format_duration_hours(23.5, "ehp"), "~23hr 30min ehp")

    def test_exactly_one_day(self):
        self.assertEqual(format_duration_hours(24.0, "ehp"), "~1d ehp")

    def test_days_hours_minutes(self):
        self.assertEqual(format_duration_hours(26.5, "ehp"), "~1d 2hr 30min ehp")

    def test_days_no_hours_no_minutes(self):
        self.assertEqual(format_duration_hours(48.0, "ehp"), "~2d ehp")

    def test_days_no_minutes_with_hours(self):
        self.assertEqual(format_duration_hours(25.0, "ehp"), "~1d 1hr ehp")

    def test_large_value_days(self):
        self.assertEqual(format_duration_hours(100.0, "ehb"), "~4d 4hr ehb")
