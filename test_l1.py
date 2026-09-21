"""Independent limits and regression guards for physics, units and input integrity."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
from l1 import count, closed_count, correction, crossing, mobility, E_CHARGE


class PhysicsTests(unittest.TestCase):
    def test_published_gates(self):
        for ef, expected in [(0, 1), (.073, 2), (.1, 2.6), (.2, 5.1)]:
            self.assertAlmostEqual(correction(ef, 300, .04), expected, delta=.01)

    def test_closed_form_over_sweep(self):
        for ef in np.linspace(0, .25, 26):
            self.assertAlmostEqual(count(ef, 300, .04, fermi_referenced=True)
                                   / closed_count(ef, 300, .04), 1, delta=5e-6)

    def test_slope_cancellation_and_monotonicity(self):
        self.assertAlmostEqual(correction(.1, 300, .02), correction(.1, 300, .08), places=12)
        self.assertTrue(np.all(np.diff([correction(x, 300, .04)
                                       for x in np.linspace(0, .25, 26)]) > 0))

    def test_units_and_fixed_resistivity(self):
        # 1e12 cm^-2 = 1e16 m^-2; SI mobility converted back by 1e4.
        self.assertAlmostEqual(mobility(1e12, 500), 1e4 / (E_CHARGE * 1e16 * 500))
        self.assertAlmostEqual(mobility(1e12, 500) / mobility(2e12, 500), 2)

    def test_invalid_parameters(self):
        for ef, temp, c in [(-.1, 300, .04), (2.5, 300, .04), (.1, 0, .04),
                            (.1, 300, -1), (float('nan'), 300, .04)]:
            with self.assertRaises(ValueError):
                correction(ef, temp, c)
        with self.assertRaises(ValueError):
            mobility(1e12, 0)

    def test_crossings_and_bracket_rejection(self):
        for target in [2, 4]:
            x = crossing(target, 300, .04, .03, .25)
            self.assertAlmostEqual(correction(x, 300, .04), target, places=10)
        with self.assertRaises(ValueError):
            crossing(10, 300, .04, .03, .25)

    def test_integrity_rejects_corruption(self):
        import hashlib
        import json
        from reproduce import verify_manifest
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'x.csv').write_bytes(b'original')
            (root / 'manifest.json').write_text(json.dumps({'files': [
                {'name': 'x.csv', 'bytes': 8, 'sha256': hashlib.sha256(b'original').hexdigest()}]}))
            self.assertTrue(verify_manifest(root)[0]['passed'])
            (root / 'x.csv').write_bytes(b'changed!')
            with self.assertRaises(ValueError):
                verify_manifest(root)


if __name__ == '__main__':
    unittest.main()
