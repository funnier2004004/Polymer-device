"""Independent checks of the prescribed L3 inverse and uncertainty."""
import unittest
import importlib.util
from pathlib import Path
import numpy as np


class L3Tests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('l3'), 'L3 implementation is missing')
        import l3
        self.mod = l3
        self.A = np.load(Path(__file__).parent/'data/regular_G05/L3_A.npy')
        self.d = np.loadtxt(Path(__file__).parent/'data/regular_G05/L3_d.csv', delimiter=',')

    def test_gradient_has_only_neighbour_differences(self):
        L = self.mod.gradient_matrix()
        self.assertEqual(L.shape, (180,100))
        np.testing.assert_array_equal(L@np.ones(100), np.zeros(180))
        for row in L:
            minus, plus = np.flatnonzero(row == -1), np.flatnonzero(row == 1)
            self.assertEqual(len(minus), 1); self.assertEqual(len(plus), 1)
            a,b = int(minus[0]),int(plus[0])
            self.assertTrue(b-a == 10 or (b-a == 1 and a//10 == b//10))

    def test_input_validation(self):
        self.mod.validate(self.A,self.d)
        for A,d in [(self.A[:127],self.d),(self.A,self.d.T),(self.A+1,self.d),
                    (self.A,self.d*np.nan)]:
            with self.assertRaises(ValueError): self.mod.validate(A,d)

    def test_solver_matches_guide_and_zero_mean(self):
        inv=self.mod.Inverse(self.A)
        P=np.eye(100)-np.ones((100,100))/100
        L=inv.L; eta=1e-2*np.linalg.norm(self.A,2)**2/np.linalg.norm(L,2)**2
        self.assertAlmostEqual(inv.eta,eta)
        M=P@(self.A.T@self.A+eta*L.T@L)@P+1e-9*np.eye(100)
        rhs=P@self.A.T@self.d.mean(axis=0)
        expected=np.linalg.lstsq(M,rhs,rcond=None)[0]; expected-=expected.mean()
        np.testing.assert_allclose(inv.solve(self.d.mean(axis=0)),expected,rtol=1e-8,atol=1e-11)
        np.testing.assert_allclose(inv.solve(np.zeros(128)),0,atol=1e-14)
        np.testing.assert_allclose(inv.solve(self.A@np.ones(100)),0,atol=1e-10)
        self.assertLess(abs(inv.solve(self.d.mean(axis=0)).mean()),1e-12)

    def test_batch_matches_individual_and_preserves_rows(self):
        inv=self.mod.Inverse(self.A)
        bat=inv.solve(self.d)
        np.testing.assert_allclose(bat,np.stack([inv.solve(d) for d in self.d]),atol=1e-11)
        self.assertEqual(bat.shape,(3,100))
        with self.assertRaises(ValueError): inv.solve(np.zeros(100))

    def test_resolution_formula_and_synthetic_positions(self):
        # Four equally weighted neighbours at radius 0.6 => sigma=sqrt(.18).
        m=np.zeros((10,10)); m[4,5]=m[6,5]=m[5,4]=m[5,6]=1
        self.assertAlmostEqual(self.mod.equivalent_fwhm(m,(5,5)),2.355*np.sqrt(.18))
        inv=self.mod.Inverse(self.A)
        for pos in [(5,5),(2,2)]:
            q,psf,width=self.mod.point_spread(inv,pos)
            self.assertLess(abs(q.mean()),1e-14)
            np.testing.assert_allclose(psf.ravel(),inv.solve(self.A@q),atol=1e-12)
            self.assertTrue(np.isfinite(width) and width>0)

    def test_noise_is_reproducible_and_uses_sample_sd(self):
        inv=self.mod.Inverse(self.A)
        a=self.mod.noise_limit(inv,self.d); b=self.mod.noise_limit(inv,self.d)
        np.testing.assert_array_equal(a['noise'],b['noise'])
        sigma=self.d.std(axis=0,ddof=1)
        expected=np.random.default_rng(60280503).normal(0,sigma,(500,128))
        np.testing.assert_array_equal(a['noise'],expected)
        maxima=np.max(abs(inv.solve(expected)),axis=1)
        np.testing.assert_allclose(a['maxima'],maxima)
        self.assertEqual(a['delta95'],float(np.percentile(maxima,95)))

    def test_threshold_decisions_and_exact_boundaries(self):
        decide=self.mod.decision
        self.assertIsNone(decide(.5,.125,None)['pass'])
        self.assertIs(decide(.5,.125,1)['pass'],True)
        self.assertIs(decide(.5,.125,.25)['pass'],False)
        for t in [.375,.5,.625]:
            r=decide(.5,.125,t)
            self.assertIsNone(r['pass']); self.assertEqual(r['status'],'borderline')
        for t in [0,-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError): decide(.5,.125,t)

    def test_features_use_row_major_xy_and_sign(self):
        m=np.zeros(100); m[12]=.3; m[86]=-.2
        f=self.mod.features(m)
        self.assertEqual([(x['row'],x['column'],x['sign']) for x in f],[(1,2,'positive'),(8,6,'negative')])
        self.assertAlmostEqual(f[0]['x_probe_pitch'],-1.5)
        self.assertAlmostEqual(f[0]['y_probe_pitch'],-2.1)
        self.assertEqual(f[1]['amplitude_fraction'],-.2)

    def test_delivery_preserves_prior_phases_and_template(self):
        self.assertIsNotNone(importlib.util.find_spec('l3_delivery'), 'L3 delivery missing')
        from l3_delivery import result_payload
        import json
        template=json.loads((Path(__file__).parent/'data/regular_G05/results_template.json').read_text())
        template['L1']['correction_factor']=2.269
        template['L2']['EF_trajectory_eV']=[.01,.02]
        analysis=self.mod.analyse(self.A,self.d)
        result=result_payload(template,analysis,'test-commit')
        self.assertEqual(result['L1'],template['L1'])
        self.assertEqual(result['L2'],template['L2'])
        self.assertEqual(set(result['L3']),set(template['L3']))
        self.assertEqual(len(result['L3']['map']),100)
        self.assertIsNone(result['L3']['pass'])
        self.assertIn('threshold',result['L3']['confidence'])
        self.assertEqual(template['L3']['map'],[])

    def test_cli_accepts_l3_and_documents_threshold(self):
        import subprocess,sys
        proc=subprocess.run([sys.executable,'reproduce.py','--help'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0)
        self.assertIn('--l3-threshold',proc.stdout)
        self.assertIn('L3',proc.stdout)


if __name__=='__main__': unittest.main()
