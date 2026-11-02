"""Bundle the existing App + existing backend, excluding state, keys and caches."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

UI = Path(__file__).resolve().parent
REPO = UI.parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, default=Path('/tmp/CFP-app-review.zip'))
args = parser.parse_args()
if not (UI/'app-dist/index.html').is_file():
    raise SystemExit('Run npm run build first')
paths = list((UI/'app-dist').glob('*'))
paths += list((UI/'public').glob('*'))
paths += [UI/name for name in ['build.mjs', 'pwa-icon.mjs', 'token-css.mjs', 'template.config.json', 'package-review.py', 'integration/source-pins.json', 'evidence/training-basic-v1.json']]
paths += [REPO/'registry/ai-entity-registry.json']
paths += [REPO/'pilots/spacex'/name for name in ['operations.py', 'operations_server.py', 'pilot.py', 'registry.json']]
paths += list((REPO/'pilots/spacex/ui').glob('*'))
paths += [UI/name for name in ['README.md', 'package.json', 'package-lock.json', 'capacitor.config.json', 'THIRD_PARTY_NOTICES.txt']]
# Native projects are source scaffolds. Never package generated signing state.
for directory in [UI/'android', UI/'ios']:
    for path in directory.rglob('*'):
        parts = path.relative_to(directory).parts
        if any(part in ['.gradle', '.idea', 'build', 'Pods', 'DerivedData', 'capacitor-cordova-android-plugins'] for part in parts):
            continue
        if 'assets' in parts or 'public' in parts:
            continue
        if path.name == 'local.properties' or path.suffix in ['.keystore', '.jks', '.mobileprovision']:
            continue
        paths.append(path)
paths = sorted(set(path for path in paths if path.is_file() and not path.is_symlink()))
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
manifest = {'source_commit': revision, 'scope': 'Local App/API review bundle; no hosted endpoint or production credentials', 'files': {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
args.output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in paths:
        archive.write(path, str(path.relative_to(REPO)))
    archive.writestr('BUILD-MANIFEST.json', json.dumps(manifest, indent=2))
    archive.writestr('REVIEW-START.txt', 'CFP+ local review only. Extract, cd pilots/spacex, then run:\npython3 operations_server.py --state-dir /tmp/cfp-app-review-state --port 8765 --provision-demo\nThe App is served at /app/ on that local server; Website uses /. Both share the same existing Operations data.\nDemo accounts/password are explicit synthetic fixtures in operations.py, not real credentials. No external backend, native signing or Production acceptance is included.\nNative projects are source scaffolds: run npm ci and npm run native:sync from hub69/ui to regenerate required assets.\n')
print(json.dumps({'artifact': str(args.output), 'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(), 'bytes': args.output.stat().st_size, 'source_commit': revision}))
