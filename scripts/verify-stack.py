#!/usr/bin/env python3
"""Exercise the real container stack through its public HTTP port.

Use --recreate to recreate this project's containers and verify persistent data.
Only test-created posts are deleted. Existing application data is left alone.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8083')
parser.add_argument('--recreate', action='store_true')
args = parser.parse_args()
base = args.url.rstrip('/')

def request(path, method='GET', body=None, expected=200):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={'Content-Type': 'application/json'})
    try:
        response = urllib.request.urlopen(req, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        payload = response.read().decode()
        assert response.status == expected, f'{method} {path}: HTTP {response.status}'
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return payload

def passed(message):
    print('PASS: ' + message, flush=True)

print('Application verification: ' + datetime.now(timezone.utc).isoformat(), flush=True)
assert '<html' in request('/').lower()
assert '<html' in request('/add-blog').lower()
passed('Frontend and direct SPA navigation respond')
ready = request('/health/ready')
assert ready['mongodb'] and ready['redis']
passed('Backend, MongoDB, and Redis are ready through the Nginx proxy')
request('/api/posts', 'POST', {}, expected=400)
passed('Invalid post is rejected')
identifier = None
email = 'ci-smoke-' + uuid.uuid4().hex + '@example.invalid'
try:
    password = uuid.uuid4().hex
    signup = request('/api/auth/email-password/signup', 'POST', {
        'name': 'Container Verification', 'email': email, 'password': password,
    })
    assert signup['success'] and signup['accessToken']
    signin = request('/api/auth/email-password/signin', 'POST', {
        'email': email, 'password': password,
    })
    assert signin['success'] and signin['accessToken']
    passed('Email/password API signup and signin use the runtime JWT secret')
    title = 'Container verification ' + uuid.uuid4().hex[:10]
    post = request('/api/posts', 'POST', {
        'title': title, 'authorName': 'Haseeb Ullah',
        'imageLink': 'https://example.com/container-demo.jpg',
        'categories': ['Travel'], 'description': 'Container integration test',
        'isFeaturedPost': True,
    })
    identifier = post['_id']
    path = '/api/posts/' + identifier
    assert request(path)['title'] == title
    assert any(p['_id'] == identifier for p in request('/api/posts'))
    passed('Create, read, and list a post backed by MongoDB')
    # Warm the list cache before changing the post.
    request('/api/posts')
    updated = title + ' updated'
    assert request(path, 'PATCH', {'title': updated})['title'] == updated
    assert next(p for p in request('/api/posts') if p['_id'] == identifier)['title'] == updated
    passed('Update is visible in both detail and cached list routes')
    if args.recreate:
        subprocess.run(['docker', 'compose', 'up', '-d', '--force-recreate',
                        '--wait', '--wait-timeout', '180'], cwd=ROOT, check=True)
        for attempt in range(30):
            try:
                if request(path)['title'] == updated:
                    break
            except (OSError, AssertionError):
                pass
            time.sleep(1)
        else:
            raise AssertionError('Post was not accessible after container recreation')
        passed('Post survives recreation of every project container using named volumes')
    request(path, 'DELETE')
    request(path, expected=404)
    assert all(p['_id'] != identifier for p in request('/api/posts'))
    identifier = None
    passed('Delete removes the post from MongoDB and cached lists')
finally:
    if identifier:
        request('/api/posts/' + identifier, 'DELETE')
    subprocess.run(['docker', 'compose', 'exec', '-T', 'backend', 'node',
                    '--input-type=module', '-e',
                    "import mongoose from 'mongoose'; import { MONGODB_URI } from './config/utils.js'; await mongoose.connect(MONGODB_URI); await mongoose.connection.collection('users').deleteOne({email:process.argv[1]}); await mongoose.disconnect();",
                    email], cwd=ROOT, check=True)
print('All requested checks passed.', flush=True)
