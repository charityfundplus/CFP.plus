"""Prepare pinned existing HUB/Core assets outside the public site. Never serve/deploy."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI_REVISION = '8ca11c26fbe3ba76db75ae1aa62b204744233d85'
CORE_REVISION = '06f386b1ba52358779cec6bc26c2d88f6a33664a'
UI_PATH = 'hub69/ui'
CLIENT_PATH = 'drafts/si-office/public/registry-client.js'

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

def materialize(revision, prefix, destination):
    """Use regular blobs only, preserving the exact pinned bytes and file hashes."""
    receipt = []
    listing = git('ls-tree', '-rz', revision, '--', prefix)
    for entry in listing.split(b'\0'):
        if not entry:
            continue
        metadata, raw_path = entry.split(b'\t', 1)
        mode, kind, blob = metadata.decode().split()
        path = raw_path.decode()
        if mode not in {'100644', '100755'} or kind != 'blob':
            raise ValueError('Unsupported source entry: ' + path)
        if Path(path).is_absolute() or '..' in Path(path).parts:
            raise ValueError('Unsafe source path')
        content = git('cat-file', 'blob', blob)
        target = destination/path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        receipt.append({'path': path, 'gitBlobSHA': blob,
                        'sha256': hashlib.sha256(content).hexdigest()})
    if not receipt:
        raise ValueError('Pinned source missing: ' + prefix)
    return receipt

def prepare(output):
    output = Path(output).resolve()
    if output == ROOT or ROOT in output.parents or output.exists():
        raise ValueError('Use a new output directory outside the source/public tree')
    if not output.parent.is_dir():
        raise ValueError('Output parent must already exist')
    # A private local artifact, not an HTTPS environment or access-control grant.
    with tempfile.TemporaryDirectory(prefix='cfp-core-reuse-', dir=output.parent) as temp:
        work = Path(temp)
        receipt = materialize(UI_REVISION, UI_PATH, work)
        receipt += materialize(CORE_REVISION, CLIENT_PATH, work)
        receipt += materialize('835616308111f6851c0387fa9f5eda60c9ffa624',
                               'registry/ai-entity-registry.json', work)
        ui = work/UI_PATH
        pins = json.loads((ui/'integration/source-pins.json').read_text())
        if pins['codex1Revision'] != CORE_REVISION:
            raise ValueError('UI/Core revision mismatch')
        client = work/CLIENT_PATH
        expected = next(f['sha256'] for f in pins['files'] if f['path'] == CLIENT_PATH)
        if hashlib.sha256(client.read_bytes()).hexdigest() != expected:
            raise ValueError('UI/Core client integrity mismatch')
        subprocess.run(['node', 'build.mjs'], cwd=ui, check=True, capture_output=True)
        if (ui/'core-dist/registry.js').read_text() != 'window.HUB69_DATA={records:[],activationAllowed:false,published:false};\n':
            raise ValueError('Core output must contain no bundled Registry rows')
        bundle = work/'bundle'; bundle.mkdir(mode=0o700)
        shutil.copytree(ui/'core-dist', bundle/'hub69-assets')
        shutil.copyfile(client, bundle/'registry-client.js')
        artifacts = {str(p.relative_to(bundle)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(bundle.rglob('*')) if p.is_file()}
        plan = {'uiRevision': UI_REVISION, 'coreRevision': CORE_REVISION,
                'sourceFiles': receipt, 'artifacts': artifacts,
                'mode': 'core', 'status': 'UNMOUNTED LOCAL PREPARATION',
                'activationAllowed': False, 'published': False, 'registryWrites': 0,
                'api': '/api/core/', 'client': '/registry-client.js',
                'session': 'existing same-origin Core cookie; no token input/storage',
                'surfaces': ['Website', 'App web surface', '8682 read-only reference'],
                'commerce': {'id': '8682', 'bindingVerified': False,
                             'ordersEnabled': False, 'paymentEnabled': False},
                'mountBlockers': ['Existing p2-http asset allowlist has no HUB UI mount',
                                 'Relative UI asset URLs need route review before mounting /69',
                                 'Approved private HTTPS origin, account and Registry read mount missing',
                                 'Actual iPhone Safari acceptance missing']}
        (bundle/'MOUNT_PLAN.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n')
        # Atomic publication of local files only. Never copy into the website.
        bundle.rename(output)
    return plan

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    plan = prepare(args.output)
    print(json.dumps({'status': plan['status'], 'activationAllowed': False,
                      'artifacts': len(plan['artifacts'])}))
