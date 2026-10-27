"""Built-in smoke/regression tests for the original DubStudio v1.0 core."""
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
import soundfile as sf
from dubstudio import core


class CoreTests(unittest.TestCase):
    def test_save_load_keeps_parts_segments_and_takes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / 'unpacked'
            root.mkdir()
            (root / 'video.mp4').write_bytes(b'example video data')
            sf.write(root / 'original.wav', np.zeros(core.RATE), core.RATE)
            take_name = 'take.wav'
            sf.write(root / take_name, np.full(core.RATE // 4, .4), core.RATE)
            seg = core.Segment(0.0, .5, transcript='Hello', reference='Hi', take=take_name, part_id=3)
            project = core.Project(root, 1.0, 'en', 'video.mp4', [seg], '', 'file',
                                   [core.Part(0, 1, 3)], True)
            dest = base / 'example.dubstudio'
            core.save_project(project, dest)
            with zipfile.ZipFile(dest) as z:
                self.assertTrue({'project.json', 'original.wav', 'video.mp4', take_name} <= set(z.namelist()))
            reopened = core.load_project(dest)
            try:
                self.assertEqual(reopened.language, 'en')
                self.assertEqual(reopened.segments[0].reference, 'Hi')
                self.assertEqual(reopened.segments[0].take, 'take.wav')
                self.assertEqual(reopened.parts[0].id, 3)
                self.assertTrue(reopened.parts_confirmed)
            finally:
                import shutil
                shutil.rmtree(reopened.root)

    def test_render_preserves_silence_and_take_position(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sf.write(root / 'take.wav', np.full(core.RATE // 5, .25), core.RATE)
            project = core.Project(root, 1.0, segments=[core.Segment(.25, .45, take='take.wav')])
            dest = root / 'mix.wav'
            core.render_dub(project, dest)
            audio, rate = sf.read(dest, dtype='float32')
            self.assertEqual(rate, core.RATE)
            self.assertEqual(len(audio), core.RATE)
            self.assertAlmostEqual(float(np.max(np.abs(audio[:int(.2*rate)]))), 0, places=4)
            self.assertGreater(float(np.mean(np.abs(audio[int(.3*rate):int(.4*rate)]))), .2)
            self.assertAlmostEqual(float(np.max(np.abs(audio[int(.5*rate):]))), 0, places=4)

    def test_timed_subtitles(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'reference.srt'
            p.write_text('1\n00:00:00,100 --> 00:00:00,550\nHello!\n\n2\n00:00:00,600 --> 00:00:01,000\nBye.\n', encoding='utf-8')
            kind, cues = core.parse_reference(p)
            self.assertEqual(kind, 'timed')
            self.assertEqual(len(cues), 2)
            self.assertEqual(cues[0][2], 'Hello!')
            segments = core.segments_from_timed_items(cues, 0, 1.0)
            self.assertEqual(len(segments), 2)

    def test_archive_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                core.safe_member(Path(tmp), '../outside.wav')

    def test_mix_export_wav(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'video.mp4').write_bytes(b'not used for WAV export')
            project = core.Project(root, .75, video='video.mp4')
            dest = root / 'export.wav'
            core.export_project(project, dest, 'WAV')
            self.assertAlmostEqual(sf.info(dest).duration, .75, places=3)


if __name__ == '__main__':
    unittest.main()
