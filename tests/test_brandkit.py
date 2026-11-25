import sys
import tempfile
import unittest
import xml.dom.minidom
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brand"))
import brandkit as bk  # noqa: E402

WORDS = '{"em": 1000, "space": 221, "words": {"Test": {"d": "M0 0 L500 0 L500 -700 L0 -700 Z", "width": 500}}}'


class BrandKit(unittest.TestCase):
    def test_kit_files_are_valid_svg(self):
        def colour(small):
            return bk.signature_ring("#4b5563", "#8b95a1", small) + bk.path(bk.flame(128, 70, 180, 30), "url(#e)", 10) + (
                "" if small else bk.sparks([(160, 60, 5), (174, 72, 8), (190, 84, 5)]))

        def mono(c):
            return f'<g fill="{c}"><path fill-rule="evenodd" d="{bk.ring()}"/><path d="{bk.flame(128, 70, 180, 30)}"/></g>'

        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "w.json").write_text(WORDS)
            files = bk.write_kit(Path(d) / "kit", "Test", colour, mono, defs=bk.gradient("e", 70, 180),
                                 name=bk.Wordmark(Path(d) / "w.json", [("Test", "#fff")]), signature="#4b5563")
            self.assertEqual(len(files), 9)
            for f in files:
                xml.dom.minidom.parse(str(Path(d) / "kit" / f))

    def test_open_ring_is_one_piece(self):
        self.assertEqual(bk.open_ring().count("M"), 1)
        self.assertEqual(bk.ring().count("M"), 2)


if __name__ == "__main__":
    unittest.main()
