import unittest

from ironforgedcore.common.time import format_duration_hours


class TestFormatDurationHours(unittest.TestCase):
    def test_none_returns_dash(self):
        self.assertEqual(format_duration_hours(None, "ehp"), "-")

    def test_none_with_no_suffix_returns_dash(self):
        self.assertEqual(format_duration_hours(None), "-")

    def test_zero_hours_returns_zero_minutes(self):
        self.assertEqual(format_duration_hours(0, "ehp"), "0 min ehp")

    def test_sub_minute_rounds_up_to_one_minute(self):
        self.assertEqual(format_duration_hours(0.001, "ehp"), "1 min ehp")

    def test_under_one_minute_uses_minute_bucket(self):
        self.assertEqual(format_duration_hours(0.5 / 60, "ehp"), "1 min ehp")

    def test_minutes_only(self):
        self.assertEqual(format_duration_hours(5 / 60, "ehp"), "5 min ehp")

    def test_minutes_only_with_ehb_suffix(self):
        self.assertEqual(format_duration_hours(45 / 60, "ehb"), "45 min ehb")

    def test_exactly_one_hour_no_minutes(self):
        self.assertEqual(format_duration_hours(1.0, "ehp"), "1 hr ehp")

    def test_hours_and_minutes(self):
        self.assertEqual(format_duration_hours(1.0 + 5 / 60, "ehp"), "1 hr 5 min ehp")

    def test_multiple_hours(self):
        self.assertEqual(format_duration_hours(3.5, "ehp"), "3 hr 30 min ehp")

    def test_hours_minutes_rounding(self):
        self.assertEqual(format_duration_hours(2.25, "ehp"), "2 hr 15 min ehp")

    def test_minutes_rounding_to_next_hour(self):
        self.assertEqual(format_duration_hours(2.999, "ehp"), "3 hr ehp")

    def test_just_under_one_day(self):
        self.assertEqual(format_duration_hours(23.5, "ehp"), "23 hr 30 min ehp")

    def test_exactly_one_day(self):
        self.assertEqual(format_duration_hours(24.0, "ehp"), "1 d ehp")

    def test_days_hours_minutes(self):
        self.assertEqual(format_duration_hours(26.5, "ehp"), "1 d 2 hr 30 min ehp")

    def test_days_no_hours_no_minutes(self):
        self.assertEqual(format_duration_hours(48.0, "ehp"), "2 d ehp")

    def test_days_no_minutes_with_hours(self):
        self.assertEqual(format_duration_hours(25.0, "ehp"), "1 d 1 hr ehp")

    def test_large_value_days(self):
        self.assertEqual(format_duration_hours(100.0, "ehb"), "4 d 4 hr ehb")

    def test_no_suffix_omits_label(self):
        self.assertEqual(format_duration_hours(2.5), "2 hr 30 min")

    def test_explicit_none_suffix_omits_label(self):
        self.assertEqual(format_duration_hours(2.5, None), "2 hr 30 min")

    def test_empty_string_suffix_omits_label(self):
        self.assertEqual(format_duration_hours(2.5, ""), "2 hr 30 min")
