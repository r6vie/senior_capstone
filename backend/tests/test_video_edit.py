import unittest

from video_edit import build_ass, plan_cuts
from video_transcribe import Word


def words(*items) -> list[Word]:
    return [Word(text, start, end) for text, start, end in items]


class PlanCutsTests(unittest.TestCase):
    def test_drops_fillers_and_splits_around_them(self):
        segments, captions = plan_cuts(words(("Um,", 0.0, 0.3), ("so", 0.4, 0.6), ("uh", 0.65, 0.9), ("then", 0.95, 1.2)))
        self.assertEqual([w.text for w in captions], ["so", "then"])
        self.assertEqual(len(segments), 2)

    def test_collapses_long_pauses(self):
        segments, captions = plan_cuts(words(("hello", 0.0, 0.4), ("there", 3.0, 3.4)))
        self.assertEqual(len(segments), 2)
        self.assertLess(captions[1].start, 1.0)

    def test_keeps_short_pauses_in_one_segment(self):
        segments, _ = plan_cuts(words(("hello", 0.0, 0.4), ("there", 0.6, 1.0)))
        self.assertEqual(len(segments), 1)

    def test_caption_times_follow_edited_timeline(self):
        segments, captions = plan_cuts(words(("a", 1.0, 1.5), ("b", 5.0, 5.5)))
        durations = sum(s.end - s.start for s in segments)
        self.assertAlmostEqual(captions[1].end, durations - 0.08, places=2)

    def test_no_speech_returns_nothing(self):
        self.assertEqual(plan_cuts(words(("um", 0.0, 0.2))), ([], []))


class CaptionTests(unittest.TestCase):
    def test_groups_words_into_dialogue_lines(self):
        ass = build_ass(words(*[(f"w{i}", i * 0.5, i * 0.5 + 0.4) for i in range(7)]), 1080, 1920)
        self.assertEqual(ass.count("Dialogue:"), 3)
        self.assertIn("{\\k40}w0", ass)


if __name__ == "__main__":
    unittest.main()
