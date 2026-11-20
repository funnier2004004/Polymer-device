import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
import numpy as np


class RevisionTests(unittest.TestCase):
    def test_blind_validation_and_three_outputs(self):
        import unified
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); data=root/'synthetic'; data.mkdir(); out=root/'output'
            for name in ['manifest.json','results_template.json','L1_params.json','L2_meta.json','L3_meta.json']:
                (data/name).write_text(json.dumps({'group':'G05','dataset_set':'blind'}))
            unified.validate_blind(data)
            payload={'pipeline_commit':'abc','L1':{'n':1},'L2':{},'L3':{}}
            def fake(args):
                args.out.mkdir(parents=True); (args.out/'results.json').write_text(json.dumps(payload))
                (args.out/'run_log.txt').write_text('synthetic calculation log')
            from argparse import Namespace
            with patch('unified.run_all',side_effect=fake),patch('unified.git_info',return_value='abc'),patch('unified.verify_manifest',return_value=[]):
                unified.run_blind(Namespace(data_dir=data,out=out,l3_threshold=.03,phase='blind'))
            self.assertEqual(json.loads((out/'blind_results.json').read_text()),payload)
            self.assertEqual((out/'pipeline_commit.txt').read_text().strip(),'abc')
            self.assertIn('synthetic calculation log',(out/'run_log.txt').read_text())
            with self.assertRaises(ValueError): unified.run_blind(Namespace(data_dir=data,out=out,l3_threshold=.03,phase='blind'))
            (data/'L2_meta.json').write_text(json.dumps({'group':'G01','dataset_set':'blind'}))
            with self.assertRaises(ValueError): unified.validate_blind(data)
            (data/'L2_meta.json').unlink()
            with self.assertRaises(ValueError): unified.validate_blind(data)

    def test_eta_diagnostics_use_candidate_noise(self):
        from unified import eta_diagnostics
        from l3 import analyse
        A=np.load('data/regular_G05/L3_A.npy'); d=np.loadtxt('data/regular_G05/L3_d.csv',delimiter=',')
        a=analyse(A,d,.03); rows=eta_diagnostics(a,d,.03)
        self.assertEqual(len(rows),5)
        self.assertAlmostEqual(rows[2]['delta95'],a['noise']['delta95'])
        self.assertAlmostEqual(rows[2]['amplitude'],a['amplitude'])
        self.assertEqual(rows[2]['decision'],'clear_fail')
        self.assertEqual(rows[2]['map_change_norm'],0)


if __name__=='__main__': unittest.main()
