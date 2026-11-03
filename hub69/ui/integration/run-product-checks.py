"""One entry point for existing product suites; no deploy, credentials or shared data."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

UI=Path(__file__).resolve().parents[1]
REPO=UI.parents[1]
out=Path(os.environ['CFP_PRODUCT_EVIDENCE_DIR']) if os.environ.get('CFP_PRODUCT_EVIDENCE_DIR') else Path(tempfile.mkdtemp(prefix='cfp-product-checks-'))
out.mkdir(parents=True,exist_ok=True)
ctttc_python=Path('/workspace/.cfp-env/venv/bin/python')
if not ctttc_python.is_file():ctttc_python=Path(sys.executable)
commands=[
 ('build',UI,['node','build.mjs']),
 ('pwa-unit',UI,['npm','test']),
 ('backend-website',REPO/'pilots/spacex',[sys.executable,'-m','unittest','-v','test_pilot','test_operations','test_operations_http','test_app_bridge','test_forum','test_website','test_social_worker']),
 ('strict-https',UI,[sys.executable,'-m','unittest','-v','integration.test_local_tls']),
 ('social-feed-race',UI,[sys.executable,'-m','unittest','-v','integration.test_social_feed']),
 ('app-browser',UI,[sys.executable,'integration/app-shared-browser.py']),
 ('social-intake-browser',UI,[sys.executable,'integration/social-intake-browser.py']),
 ('ctttc',REPO,[str(ctttc_python),'run_ctttc_v066_tests.py']),
 ('unicode',REPO,[str(ctttc_python),'-m','tests.ctttc.duplicate_unicode_regression_v066']),
]
results=[]
env=dict(os.environ,CFP_APP_EVIDENCE_DIR=str(out/'browser'),CFP_SOCIAL_EVIDENCE_DIR=str(out/'social-browser'),PYTHONDONTWRITEBYTECODE='1',npm_config_cache='/workspace/.cfp-env/npm-cache')
for name,cwd,argv in commands:
    with (out/(name+'.txt')).open('w') as log:
        result=subprocess.run(argv,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
    record={'name':name,'exit_code':result.returncode,'status':'PASS' if result.returncode==0 else 'FAIL','log':name+'.txt'}
    results.append(record);print(json.dumps(record),flush=True)
report={'scope':'Local product suites; real HTTP/SQLite/browser and strict local TLS; not external staging/physical device','results':results,'all_passed':all(r['exit_code']==0 for r in results)}
(out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print('Evidence directory:',out)
raise SystemExit(0 if report['all_passed'] else 1)
