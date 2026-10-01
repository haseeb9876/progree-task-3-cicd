#!/usr/bin/env python3
"""Record build identities and verify deployment uses those same images."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
output = root / '.ci-artifacts/image-manifest.json'
revision = os.environ['APP_REVISION']
tag = os.environ['IMAGE_TAG']

def inspect(*args):
    return json.loads(subprocess.check_output(['docker', *args], cwd=root, text=True))[0]

if sys.argv[1] == 'capture':
    manifest = []
    for service in ('frontend', 'backend'):
        image = f'progree-task3-{service}:{tag}'
        info = inspect('image', 'inspect', image)
        assert info['Config']['Labels']['org.opencontainers.image.revision'] == revision
        manifest.append({'service': service, 'image': image, 'id': info['Id'],
                         'revision': revision, 'size_bytes': info['Size']})
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + '\n')
    print('Recorded both built image identities and commit labels.')
elif sys.argv[1] == 'verify':
    for item in json.loads(output.read_text()):
        image = inspect('image', 'inspect', item['image'])
        assert image['Id'] == item['id'], 'Loaded image differs from build output'
        container_id = subprocess.check_output(['docker', 'compose', 'ps', '-q', item['service']], cwd=root, text=True).strip()
        running = inspect('inspect', container_id)
        assert running['Image'] == item['id'], 'Running container differs from tested build'
        assert running['Config']['Labels']['org.opencontainers.image.revision'] == revision
    print('PASS: Both running application images match the build job and pushed revision.')
else:
    raise SystemExit('Usage: images.py capture|verify')
