#!/usr/bin/env python3
"""Add three clearly labelled demo posts; skip titles that already exist."""
import argparse
import json
import urllib.request
parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8083')
args = parser.parse_args()
url = args.url.rstrip('/') + '/api/posts'
with urllib.request.urlopen(url, timeout=15) as response:
    existing = {post['title'] for post in json.load(response)}
posts = [
    ('Exploring the mountains', 'Mountains', 'https://i.ibb.co/3z72vmc/clean-lake-mountains-range-trees-nature-4k.webp'),
    ('A day in London', 'City', 'https://i.ibb.co/BNjv5Nn/London-Skyline-125508655.webp'),
    ('An island escape', 'Beaches', 'https://i.ibb.co/52mk2Yq/sunset-pier.webp'),
]
for title, category, image in posts:
    if title in existing:
        continue
    body = json.dumps({'title': title, 'authorName': 'Internship Demo',
                       'imageLink': image, 'categories': [category, 'Travel'],
                       'description': 'Sample travel content for the Progree DevOps containerization demonstration.',
                       'isFeaturedPost': True}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as response:
        assert response.status == 200
    print('Added demo post: ' + title)
