import copy, hashlib, sqlite3, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from pilot import import_snapshot, export_ui, fixture, writeback, ROOT

class PilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.rows = fixture(ROOT / 'registry.json')
    def tearDown(self):
        self.tmp.cleanup()
    def test_import_readback_ui_and_source_unchanged(self):
        src = ROOT/'registry.json'; before = src.read_bytes()
        self.assertEqual(import_snapshot(self.rows,self.root,enabled=True),'IMPORTED')
        ui=self.root/'ui';ui.mkdir()
        result=export_ui(self.root,ui)
        self.assertEqual(result['records'],self.rows)
        self.assertEqual(result['audit'][0][0],'IMPORT')
        self.assertEqual(src.read_bytes(),before)
        self.assertTrue((ui/'snapshot.js').is_file())
    def test_idempotency(self):
        import_snapshot(self.rows,self.root,enabled=True)
        before=(self.root/'pilot.sqlite').read_bytes()
        self.assertEqual(import_snapshot(self.rows,self.root,enabled=True),'UNCHANGED')
        self.assertEqual((self.root/'pilot.sqlite').read_bytes(),before)
    def test_kill_switch_before_io(self):
        dest=self.root/'absent'
        with self.assertRaisesRegex(PermissionError,'KILL_SWITCH_OFF'):
            import_snapshot(self.rows,dest)
        self.assertFalse(dest.exists())
    def test_writeback_before_io(self):
        with patch('pilot.sqlite3.connect',side_effect=AssertionError('I/O attempted')):
            with self.assertRaisesRegex(PermissionError,'WRITEBACK_BLOCKED'):
                import_snapshot(self.rows,self.root,enabled=True,reverse=True)
            with self.assertRaises(PermissionError): writeback()
    def test_validation(self):
        for key,val in [('id','SpaceX'),('parent_id','new'),('name','<script>'),('status','secret'),('extra','token')]:
            bad=copy.deepcopy(self.rows);bad[0][key]=val
            with self.subTest(key=key), self.assertRaises(ValueError):
                import_snapshot(bad,self.root,enabled=True)
        self.assertFalse((self.root/'pilot.sqlite').exists())
    def test_duplicate(self):
        with self.assertRaises(ValueError):import_snapshot(self.rows*2,self.root,enabled=True)
    def test_symlink(self):
        target=self.root/'source';target.write_text('do not modify')
        (self.root/'pilot.sqlite').symlink_to(target)
        with self.assertRaises(ValueError):import_snapshot(self.rows,self.root,enabled=True)
        self.assertEqual(target.read_text(),'do not modify')
    def test_audit_idempotency(self):
        import_snapshot(self.rows,self.root,enabled=True)
        # Idempotent replay produces no audit event.
        with sqlite3.connect(self.root/'pilot.sqlite') as c:
            self.assertEqual(c.execute('SELECT count(*) FROM audit').fetchone()[0],1)

    def test_audit_failure_rolls_back_import(self):
        import_snapshot(self.rows,self.root,enabled=True)
        with sqlite3.connect(self.root/'pilot.sqlite') as c:
            c.execute('DELETE FROM snapshots')
            c.execute("CREATE TRIGGER deny_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT, 'AUDIT_FAIL'); END")
        with self.assertRaisesRegex(sqlite3.IntegrityError,'AUDIT_FAIL'):
            import_snapshot(self.rows,self.root,enabled=True)
        with sqlite3.connect(self.root/'pilot.sqlite') as c:
            self.assertEqual(c.execute('SELECT count(*) FROM snapshots').fetchone()[0],0)

if __name__=='__main__':unittest.main()
