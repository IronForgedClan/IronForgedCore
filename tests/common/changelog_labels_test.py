import unittest

from ironforgedcore.common.changelog_labels import (
    CHANGE_TYPE_LABELS,
    label_for_change_type,
)
from ironforgedcore.models.changelog import ChangeType


class TestChangelogLabels(unittest.TestCase):
    def test_change_type_labels_covers_every_enum_member(self):
        for change_type in ChangeType:
            self.assertIn(change_type, CHANGE_TYPE_LABELS)
            self.assertIsInstance(CHANGE_TYPE_LABELS[change_type], str)
            self.assertGreater(len(CHANGE_TYPE_LABELS[change_type]), 0)

    def test_label_for_change_type_returns_mapped_label(self):
        self.assertEqual(
            label_for_change_type(ChangeType.ADD_INGOTS),
            CHANGE_TYPE_LABELS[ChangeType.ADD_INGOTS],
        )
        self.assertEqual(
            label_for_change_type(ChangeType.DISCORD_ID_CHANGE),
            CHANGE_TYPE_LABELS[ChangeType.DISCORD_ID_CHANGE],
        )

    def test_label_for_change_type_unknown_returns_fallback(self):
        self.assertEqual(label_for_change_type(999), "Unknown")
