#!/usr/bin/env python3
"""Update an existing Cloud Run service; queue canonical builds and retry ABORTED only."""
import argparse
from datetime import datetime
import json
import os
import random
import re
import subprocess
import time
from pathlib import Path


class DeploymentError(RuntimeError):
    pass


def config(env):
    keys = ['PROJECT', 'REGION', 'SERVICE', 'IMAGE_REPOSITORY', 'BUILD_ID', 'BUILD_REGION', 'COMMIT_SHA', 'BRANCH']
    result = {key: env.get('CFP_' + key, '') for key in keys}
    if any(not value or value.startswith('-') for value in result.values()):
        raise DeploymentError('Missing or unsafe deployment configuration; no update attempted')
    if result['SERVICE'] != 'cfp-plus':
        raise DeploymentError('This Website pipeline may only update cfp-plus; Gateway is a separate target')
    if result['BRANCH'] != 'main':
        raise DeploymentError('Only the reviewed main trigger may deploy')
    if not re.fullmatch(r'[0-9a-f]{40}', result['COMMIT_SHA']):
        raise DeploymentError('A full Git SHA is required')
    if not re.fullmatch(r'[a-z0-9.-]+/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+', result['IMAGE_REPOSITORY']):
        raise DeploymentError('Use the existing registry/repository/image path without scheme or tag')
    return result


def run(args):
    return subprocess.run(args, text=True, capture_output=True, check=False)


def checked(args, runner):
    response = runner(args)
    if response.returncode:
        # Do not dump provider output, credential/environment values or arbitrary error bodies.
        raise DeploymentError('Metadata operation failed: ' + ' '.join(args[:4]) + '; exit=' + str(response.returncode))
    return json.loads(response.stdout)


def command(c, resource):
    return ['gcloud', *resource, '--project=' + c['PROJECT'], '--region=' + c['REGION']]


def queue(c, runner=run, sleep=time.sleep, polls=120):
    """Oldest active canonical build first; scope is project/build-region/_SERVICE.

    Other triggers, manual writers and other build regions must be excluded by
    governance. This is not a distributed lock for arbitrary Cloud Run clients.
    """
    for _ in range(polls):
        rows = checked(['gcloud', 'builds', 'list', '--project=' + c['PROJECT'], '--region=' + c['BUILD_REGION'],
                        '--filter=status=(QUEUED,WORKING)', '--limit=1000',
                        '--format=json(id,createTime,substitutions._SERVICE)'], runner)
        if not isinstance(rows, list) or len(rows) >= 1000:
            raise DeploymentError('Incomplete build queue inventory; fail closed')
        peers = [r for r in rows if r.get('substitutions', {}).get('_SERVICE') == c['SERVICE']]
        if any(not r.get('id') or not r.get('createTime') for r in peers):
            raise DeploymentError('Malformed queue metadata')
        own = next((r for r in peers if r['id'] == c['BUILD_ID']), None)
        if own is not None:
            order = lambda r: (datetime.fromisoformat(r['createTime'].replace('Z', '+00:00')), r['id'])
            if not any(order(r) < order(own) for r in peers):
                return
        sleep(5)
    raise DeploymentError('Canonical deployment queue timed out; no service update attempted')


def deploy(c, image, runner=run, sleep=time.sleep, attempts=5, polls=60):
    if not re.fullmatch(re.escape(c['IMAGE_REPOSITORY']) + r'@sha256:[0-9a-f]{64}', image):
        raise DeploymentError('Image must be an immutable digest of the configured existing repository')
    # Require an existing service. Never create a new service or change IAM/env/secrets/traffic policy.
    checked(command(c, ['run', 'services', 'describe', c['SERVICE']]) + ['--format=json(metadata.name)'], runner)
    for attempt in range(attempts):
        response = runner(command(c, ['run', 'services', 'update', c['SERVICE']]) + [
            '--platform=managed', '--image=' + image, '--quiet',
            '--update-labels=cfp-build-id=' + c['BUILD_ID'] + ',cfp-source-commit=' + c['COMMIT_SHA']])
        if response.returncode == 0:
            break
        output = response.stdout + response.stderr
        if not re.search(r'\bABORTED:\s*Conflict for resource', output):
            raise DeploymentError('Cloud Run update failed (non-retryable), exit=' + str(response.returncode))
        if attempt + 1 == attempts:
            raise DeploymentError('Cloud Run ABORTED conflict persisted after bounded retries')
        # Re-check the queue before retrying; do not overlap a known older canonical build.
        queue(c, runner, sleep)
        delay = min(60, 5 * 2 ** attempt) + random.uniform(0, 2)
        print('Cloud Run ABORTED conflict; retry', attempt + 2, 'of', attempts, flush=True)
        sleep(delay)
    else:
        raise DeploymentError('No deployment attempt configured')
    for _ in range(polls):
        value = checked(command(c, ['run', 'services', 'describe', c['SERVICE']]) + [
            '--format=json(status.conditions,status.latestCreatedRevisionName,status.latestReadyRevisionName,spec.template.spec.containers.image)'], runner)
        status = value.get('status', {})
        # Only image is requested; environment fields/values are never exported.
        containers = value.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
        ready = any(x.get('type') == 'Ready' and str(x.get('status')).lower() == 'true' for x in status.get('conditions', []))
        revision = status.get('latestCreatedRevisionName')
        if len(containers) != 1 or containers[0].get('image') != image:
            raise DeploymentError('Service image changed by another writer; review required')
        if ready and revision and revision == status.get('latestReadyRevisionName'):
            return {'build_id': c['BUILD_ID'], 'source_commit': c['COMMIT_SHA'], 'service': c['SERVICE'],
                    'project': c['PROJECT'], 'region': c['REGION'], 'image': image, 'revision': revision,
                    'cloud_run_ready': True, 'http_readback': 'NOT_RUN'}
        sleep(5)
    raise DeploymentError('Cloud Run readiness timed out; no Runtime PASS claim')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--validate-only', action='store_true')
    args = p.parse_args()
    c = config(os.environ)
    if args.validate_only:
        print('Deployment configuration valid; no Cloud mutation')
        return
    image = Path('/workspace/image-digest.txt').read_text().strip()
    queue(c)
    evidence = deploy(c, image)
    Path('/workspace/deployment-evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence), flush=True)


if __name__ == '__main__':
    try:
        main()
    except (DeploymentError, ValueError, OSError) as error:
        raise SystemExit(str(error))
