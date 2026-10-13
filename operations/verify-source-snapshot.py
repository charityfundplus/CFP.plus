"""Verify pinned source inventory or safely extract its controlled scoped ZIP."""
import argparse, hashlib, json, pathlib, zipfile

parser = argparse.ArgumentParser()
parser.add_argument('manifest', type=pathlib.Path)
parser.add_argument('manifest_sha256')
parser.add_argument('--root', type=pathlib.Path)
parser.add_argument('--archive', type=pathlib.Path)
parser.add_argument('--archive-sha256')
parser.add_argument('--extract', type=pathlib.Path)
args = parser.parse_args()
sha = lambda b: hashlib.sha256(b).hexdigest()
raw = args.manifest.read_bytes()
if sha(raw) != args.manifest_sha256:
    raise SystemExit('Manifest SHA-256 mismatch')
manifest = json.loads(raw)
files = {f['path']: f for f in manifest['files']}
def safe(name):
    p = pathlib.PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name:
        raise SystemExit('Unsafe archive/manifest path')
def verify(name, data):
    safe(name)
    f = files[name]
    if len(data) != f['bytes'] or sha(data) != f['sha256']:
        raise SystemExit('Source mismatch: ' + name)
if args.archive:
    if not args.archive_sha256 or sha(args.archive.read_bytes()) != args.archive_sha256:
        raise SystemExit('Archive SHA-256 mismatch')
    with zipfile.ZipFile(args.archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise SystemExit('Duplicate archive entries')
        selected = {n for n in files if n.startswith(('drafts/si-office/', '69/'))}
        if not selected.issubset(names):
            raise SystemExit('Incomplete source snapshot')
        for n in names:
            safe(n)
            if n in files:
                verify(n, z.read(n))
            elif n not in {'SOURCE_MANIFEST.json', 'SOURCE_MANIFEST.sha256', 'CURRENT_SOURCE_MANIFEST.sha256'}:
                raise SystemExit('Unexpected archive entry')
        if z.read('SOURCE_MANIFEST.json') != raw:
            raise SystemExit('Embedded manifest mismatch')
        if args.extract:
            if args.extract.exists():
                raise SystemExit('Extract target must be new')
            args.extract.mkdir(parents=True)
            z.extractall(args.extract)
        print('VERIFIED scoped archive:', len(selected), 'source files')
elif args.root:
    root = args.root.resolve()
    for n in files:
        safe(n)
        p = (root / n).resolve()
        if not p.is_relative_to(root):
            raise SystemExit('Source escaped root')
        verify(n, p.read_bytes())
    print('VERIFIED source inventory:', len(files), 'files')
else:
    parser.error('Provide --root or --archive')
