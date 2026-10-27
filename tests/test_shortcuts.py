import unittest
from dubstudio.shortcuts import (DEFAULT_SHORTCUTS, GROUPS, LABELS,
                                 normalise, find_conflict, overrides)


class ShortcutsTests(unittest.TestCase):
    def test_defaults_unique(self):
        self.assertIsNone(find_conflict(DEFAULT_SHORTCUTS))

    def test_every_action_has_label_and_group(self):
        actions = [action for group in GROUPS.values() for action in group]
        self.assertEqual(set(actions), set(DEFAULT_SHORTCUTS))
        for lang in ('pt', 'en', 'ja'):
            self.assertTrue(all(action in LABELS[lang] for action in actions))

    def test_override_only_changes_selected_action(self):
        merged = normalise({'play': 'F8'})
        self.assertEqual(merged['play'], 'F8')
        self.assertEqual(merged['record'], 'R')
        self.assertEqual(overrides(merged), {'play': 'F8'})

    def test_unknown_entries_not_loaded(self):
        self.assertNotIn('unknown', normalise({'unknown': 'F9'}))
        self.assertEqual(normalise({'save': ''})['save'], DEFAULT_SHORTCUTS['save'])

    def test_duplicate_rejected(self):
        conflict = find_conflict({'record': 'Space'})
        self.assertEqual(set(conflict), {'record', 'play'})

    def test_defaults_can_be_restored(self):
        self.assertEqual(overrides(DEFAULT_SHORTCUTS), {})


if __name__ == '__main__':
    unittest.main()
