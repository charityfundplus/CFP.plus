import json, os, pathlib, subprocess, tempfile, unittest, yaml
ROOT=pathlib.Path(__file__).resolve().parents[2]
PATH=ROOT/'.github/workflows/cmp-gemini-notion-pilot.yml'
NEW=yaml.safe_load(PATH.read_text()); OLD=yaml.safe_load(subprocess.check_output(['git','show','835616308111f6851c0387fa9f5eda60c9ffa624:.github/workflows/cmp-gemini-notion-pilot.yml'],cwd=ROOT,text=True))
STEPS=NEW['jobs']['run-pilot']['steps']; CALL=next(s for s in STEPS if s['name']=='Call Gemini API')
class WorkflowTests(unittest.TestCase):
 def invoke(self, status='200', body=None, transport=0, model='gemini-2.5-pro'):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp); curl=p/'curl'
   curl.write_text('#!/usr/bin/env python3\nimport json,os,sys\nfrom pathlib import Path\nPath("args.json").write_text(json.dumps(sys.argv[1:]))\nPath("gemini-response.json").write_text(os.environ["MOCK_BODY"])\nprint(os.environ["MOCK_STATUS"],end="")\nsys.exit(int(os.environ["MOCK_EXIT"]))\n'); curl.chmod(0o755)
   env=dict(os.environ,PATH=str(p)+':'+os.environ['PATH'],GEMINI_API_KEY='FAKE_TEST_KEY',GEMINI_MODEL=model,MOCK_STATUS=status,MOCK_EXIT=str(transport),MOCK_BODY=json.dumps(body if body is not None else {'candidates':[{'content':{'parts':[{'text':'READY'}]}}]}))
   r=subprocess.run(['bash','-c',CALL['run']],cwd=p,env=env,text=True,capture_output=True)
   diagnostic=json.loads((p/'gemini-call-status.json').read_text()) if (p/'gemini-call-status.json').exists() else None
   args=json.loads((p/'args.json').read_text()) if (p/'args.json').exists() else None
   self.assertNotIn('FAKE_TEST_KEY',r.stdout+r.stderr+(json.dumps(diagnostic) if diagnostic else ''))
   return r,diagnostic,args
 def test_valid_response(self):
  r,d,a=self.invoke(); self.assertEqual(r.returncode,0); self.assertEqual(d['result'],'PASS'); self.assertTrue(d['response_valid'])
 def test_404_classified(self):
  r,d,a=self.invoke('404',{'error':{'status':'NOT_FOUND','message':'FAKE_TEST_KEY'}}); self.assertNotEqual(r.returncode,0); self.assertEqual(d['provider_status'],'NOT_FOUND')
 def test_transport_timeout(self):
  r,d,a=self.invoke('000',{},28); self.assertNotEqual(r.returncode,0); self.assertEqual(d['transport_exit_code'],28)
 def test_invalid_success_body(self):
  for body in ({},[],{'candidates':[{'content':{'parts':[{'text':' '}]}}]}):
   with self.subTest(body=body):
    r,d,a=self.invoke(body=body); self.assertNotEqual(r.returncode,0); self.assertEqual(d['result'],'FAIL')
 def test_untrusted_status_redacted(self):
  r,d,a=self.invoke('403',{'error':{'status':'FAKE_TEST_KEY'}}); self.assertEqual(d['provider_status'],'UNKNOWN'); self.assertNotEqual(r.returncode,0)
 def test_invalid_model_prevents_request(self):
  for model in ('../model','model?key=secret','model;echo hacked'):
   with self.subTest(model=model):
    r,d,a=self.invoke(model=model); self.assertNotEqual(r.returncode,0); self.assertIsNone(a)
 def test_header_auth_and_timeouts(self):
  r,d,a=self.invoke(); urls=[x for x in a if x.startswith('https:')]; self.assertEqual(len(urls),1); self.assertNotIn('key=',urls[0]); self.assertIn('x-goog-api-key: FAKE_TEST_KEY',a); self.assertIn('--connect-timeout',a); self.assertIn('--max-time',a)
 def test_default_model_preserved(self): self.assertEqual(CALL['env']['GEMINI_MODEL'],"${{ vars.GEMINI_MODEL || 'gemini-2.5-pro' }}")
 def test_no_inline_secret_expression(self):
  for step in STEPS: self.assertNotIn('${{ secrets.',step.get('run',''))
 def test_notion_steps_unchanged(self):
  old=OLD['jobs']['run-pilot']['steps']; start=next(i for i,s in enumerate(old) if s['name']=='Read locked Notion page blocks'); new_start=next(i for i,s in enumerate(STEPS) if s['name']=='Read locked Notion page blocks'); self.assertEqual(old[start:],STEPS[new_start:]); self.assertTrue(all('if' not in s for s in STEPS[new_start:]))
 def test_sanitized_artifact_only(self):
  s=next(s for s in STEPS if s['name']=='Upload sanitized Gemini diagnostics'); self.assertEqual(s['if'],'always()'); self.assertEqual(s['with']['path'],'gemini-call-status.json')
 def test_bash_syntax(self):
  for step in STEPS:
   if 'run' in step:
    r=subprocess.run(['bash','-n'],input=step['run'],text=True,capture_output=True); self.assertEqual(r.returncode,0,(step['name'],r.stderr))
if __name__=='__main__': unittest.main(verbosity=2)
