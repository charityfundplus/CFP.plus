import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('prepare_core_reuse', ROOT/'scripts/prepare_core_reuse.py')
reuse = importlib.util.module_from_spec(spec); spec.loader.exec_module(reuse)

class ReuseTests(unittest.TestCase):
    def test_private_bundle_reuses_exact_client_without_snapshot_or_activation(self):
        protected = ['69/index.html', '8682/index.html', 'Dockerfile', 'nginx.conf',
                     'registry/ai-entity-registry.json', 'registry/country-route-map.json']
        before = {p: (ROOT/p).read_bytes() for p in protected}
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)/'bundle'
            plan = reuse.prepare(output)
            self.assertFalse(plan['activationAllowed']); self.assertFalse(plan['published'])
            self.assertEqual(plan['registryWrites'], 0)
            self.assertEqual(output.stat().st_mode & 0o777, 0o700)
            expected = reuse.git('show', reuse.CORE_REVISION+':'+reuse.CLIENT_PATH)
            self.assertEqual((output/'registry-client.js').read_bytes(), expected)
            self.assertIn('records:[]', (output/'hub69-assets/registry.js').read_text())
            self.assertEqual((output/'hub69-assets/config.js').read_text(), 'window.HUB69_CONFIG={mode:"core"};\n')
            self.assertIn("import('/registry-client.js')", (output/'hub69-assets/core-binding.js').read_text())
            self.assertFalse((output/'registry').exists())
            self.assertFalse(plan['commerce']['bindingVerified'])
            for path, digest in plan['artifacts'].items():
                self.assertEqual(hashlib.sha256((output/path).read_bytes()).hexdigest(), digest)
            self.assertEqual(json.loads((output/'MOUNT_PLAN.json').read_text())['coreRevision'], reuse.CORE_REVISION)
            with self.assertRaises(ValueError): reuse.prepare(output)
        self.assertEqual(before, {p: (ROOT/p).read_bytes() for p in protected})

    def test_refuses_public_source_output(self):
        with self.assertRaises(ValueError): reuse.prepare(ROOT/'69/reuse-candidate')
        with self.assertRaises(ValueError): reuse.prepare(ROOT)

if __name__ == '__main__': unittest.main(verbosity=2)
