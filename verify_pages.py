"""Verify the static bytes approved for public release before uploading a Pages artifact."""
import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path

ASSET = re.compile(r'assets/[a-zA-Z0-9][a-zA-Z0-9_-]*\.(?:html|css|js|mjs|wasm|ttf|woff2|png|jpe?g|webp|svg|mp4|webm|json|json\.gz)')
NOTICE = re.compile(r'licenses/[a-zA-Z0-9][a-zA-Z0-9_.-]*\.(?:txt|md)')
TEXT = {'.html', '.css', '.js', '.mjs', '.json', '.svg', '.txt', '.md'}
FORBIDDEN = {
    'local or internal address': re.compile(
        r'(?i)https?://(?:localhost\b|127\.\d|10\.\d|172\.(?:1[6-9]|2\d|3[01])\.\d|192\.168\.\d|[^/:\s"\']+\.internal\b)'),
    # Emscripten's /home/web_user is an in-browser virtual directory.
    'local project path': re.compile(r'(?i)(?:\b[A-Z]:[/\\]+(?:Users|papers|WRC|oldProject)\b|/(?:mnt/|Users/|home/(?!web_user\b))[^\s<>"\']+)'),
    'private source or capture': re.compile(
        r'(?i)original_project_workflow_stack|experiments/toaster_scene2/|binding\.npz|geometry-lab-web-build/v1'),
    'credential signature': re.compile(
        r'github_pat_[a-zA-Z0-9_]{20,}|gh[pousr]_[a-zA-Z0-9]{24,}|(?:AKIA|ASIA)[A-Z0-9]{16}\b|'
        r'\bsk-(?:proj-|ant-|live-)?[a-zA-Z0-9_-]{28,}|-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----'),
    'local preview build': re.compile(r'["\']?pagesPreview["\']?\s*:\s*true|子路径验收版，在本机测试'),
}

def verify(root, manifest_path):
    if not root.is_dir() or root.is_symlink() or not manifest_path.is_file():
        raise ValueError('Missing pages-dist or its reviewed file manifest.')
    review = json.loads(manifest_path.read_text(encoding='utf-8'))
    if review.get('schema') != 'spatial-lab/pages-review/v1' or review.get('visibility') != 'public' or not review.get('reviewed_by'):
        raise ValueError('A public review of the exact artifacts is required.')
    files = review['files']
    existing_site_approved = review.get('disclosure') == 'owner-approved-existing-scene2-site'
    if not isinstance(files, dict) or 'index.html' not in files:
        raise ValueError('The reviewed release needs index.html.')
    actual = set()
    for path in root.rglob('*'):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink() or not path.is_file() and not path.is_dir():
            raise ValueError(f'Unsupported filesystem entry: {rel}')
        if path.is_dir():
            if rel not in {'assets', 'licenses'}:
                raise ValueError(f'Unexpected directory: {rel}')
            continue
        if rel != 'index.html' and not ASSET.fullmatch(rel) and not NOTICE.fullmatch(rel):
            raise ValueError(f'Unexpected publication file: {rel}')
        if path.stat().st_size >= 100 * 1024 * 1024:
            raise ValueError(f'Publication file exceeds the file size limit: {rel}')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != files.get(rel):
            raise ValueError(f'File has not been reviewed at this exact SHA-256: {rel}')
        actual.add(rel)
        if rel == 'index.html' and len(raw) > 512 * 1024:
            raise ValueError('index.html must be a split static entry.')
        if path.suffix == '.wasm' and raw[:4] != b'\x00asm':
            raise ValueError(f'Invalid WebAssembly file: {rel}')
        if path.suffix in TEXT or rel.endswith('.json.gz'):
            body = (gzip.decompress(raw) if rel.endswith('.json.gz') else raw).decode('utf-8')
            for reason, pattern in FORBIDDEN.items():
                if reason == 'private source or capture' and existing_site_approved:
                    continue
                if pattern.search(body):
                    raise ValueError(f'{rel} rejected: {reason}')
            if rel == 'index.html' and re.search(r'''(?i)(?:href|src)\s*=\s*["']/[^/]''', body):
                raise ValueError('index.html contains a domain-root path.')
    if actual != set(files):
        raise ValueError('The reviewed manifest does not match the publication files.')
    print(f'PAGES_RELEASE_VERIFIED {len(actual)} files')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dist', type=Path)
    parser.add_argument('review', type=Path)
    args = parser.parse_args()
    try:
        verify(args.dist, args.review)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f'PAGES_RELEASE_BLOCKED {error}\n')
