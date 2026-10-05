import importlib.util
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('deploy', ROOT / 'scripts/deploy_cloud_run.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)

ENV = {'CFP_PROJECT':'test-project','CFP_REGION':'test-region','CFP_SERVICE':'cfp-plus',
       'CFP_IMAGE_REPOSITORY':'test-docker.pkg.dev/test-project/web/cfp-plus','CFP_BUILD_ID':'build-b',
       'CFP_BUILD_REGION':'global','CFP_COMMIT_SHA':'a'*40,'CFP_BRANCH':'main'}
IMAGE = ENV['CFP_IMAGE_REPOSITORY'] + '@sha256:' + 'b'*64


def result(code=0, data=None, error=''):
    return subprocess.CompletedProcess([], code, json.dumps(data) if data is not None else '', error)


def row(name, timestamp):
    return {'id':name,'createTime':timestamp,'substitutions':{'_SERVICE':'cfp-plus'}}


def ready(image=IMAGE):
    return {'status':{'conditions':[{'type':'Ready','status':'True'}],
                      'latestCreatedRevisionName':'cfp-plus-fixture','latestReadyRevisionName':'cfp-plus-fixture'},
            'spec':{'template':{'spec':{'containers':[{'image':image}]}}}}


class Tests(unittest.TestCase):
    def setUp(self):
        self.c = deploy.config(ENV)
        self.calls = []

    def runner(self, responses):
        iterator = iter(responses)
        def run(args):
            self.calls.append(args)
            return next(iterator)
        return run

    def test_valid_configuration_no_cloud_call(self):
        self.assertEqual(deploy.config(ENV)['SERVICE'],'cfp-plus')

    def test_configuration_fail_closed(self):
        for key,value in [('CFP_REGION',''),('CFP_SERVICE','cfp-gateway'),('CFP_BRANCH','pull-request'),('CFP_COMMIT_SHA','short'),('CFP_IMAGE_REPOSITORY','https://invalid/image')]:
            with self.subTest(key=key),self.assertRaises(deploy.DeploymentError):
                deploy.config({**ENV,key:value})

    def test_oldest_active_build_waits_before_update(self):
        sleep=[]; own=row('build-b','2026-10-05T01:00:00Z');old=row('build-a','2026-10-05T00:00:00Z')
        deploy.queue(self.c,self.runner([result(data=[old,own]),result(data=[own])]),sleep.append,polls=2)
        self.assertEqual(sleep,[5])
        self.assertFalse(any('update' in c for c in self.calls))

    def test_missing_own_queue_record_never_deploys(self):
        with self.assertRaises(deploy.DeploymentError):deploy.queue(self.c,self.runner([result(data=[])]),lambda _:None,polls=1)

    def test_foreign_service_does_not_block(self):
        other={**row('build-a','2026-10-05T00:00:00Z'),'substitutions':{'_SERVICE':'other-service'}}
        deploy.queue(self.c,self.runner([result(data=[other,row('build-b','2026-10-05T01:00:00Z')])]),lambda _:None,polls=1)

    def test_conflict_retries_same_digest_and_reads_revision(self):
        sleep=[]
        responses=[result(data={'metadata':{'name':'cfp-plus'}}),result(1,error="ERROR: (gcloud.run.services.update) ABORTED: Conflict for resource 'cfp-plus'"),
                   result(data=[row('build-b','2026-10-05T01:00:00Z')]),result(),result(data=ready())]
        evidence=deploy.deploy(self.c,IMAGE,self.runner(responses),sleep.append)
        updates=[x for x in self.calls if 'update' in x]
        self.assertEqual(len(updates),2)
        self.assertEqual(updates[0],updates[1])
        self.assertTrue(evidence['cloud_run_ready'])
        self.assertEqual(evidence['http_readback'],'NOT_RUN')
        self.assertEqual(evidence['revision'],'cfp-plus-fixture')
        self.assertTrue(sleep)

    def test_permission_error_is_not_retried(self):
        responses=[result(data={'metadata':{'name':'cfp-plus'}}),result(1,error='PERMISSION_DENIED')]
        with self.assertRaises(deploy.DeploymentError):deploy.deploy(self.c,IMAGE,self.runner(responses),lambda _:None)
        self.assertEqual(len([x for x in self.calls if 'update' in x]),1)

    def test_persistent_conflict_fails_after_bound(self):
        responses=[result(data={'metadata':{'name':'cfp-plus'}}),result(1,error='ABORTED: Conflict for resource'),result(data=[row('build-b','2026-10-05T01:00:00Z')]),result(1,error='ABORTED: Conflict for resource')]
        with self.assertRaises(deploy.DeploymentError):deploy.deploy(self.c,IMAGE,self.runner(responses),lambda _:None,attempts=2)
        self.assertEqual(len([x for x in self.calls if 'update' in x]),2)

    def test_no_service_creation_or_iam_changes(self):
        deploy.deploy(self.c,IMAGE,self.runner([result(data={'metadata':{'name':'cfp-plus'}}),result(),result(data=ready())]),lambda _:None)
        text=' '.join(' '.join(x) for x in self.calls)
        self.assertNotIn('run deploy',text)
        self.assertNotIn('allow-unauthenticated',text)
        self.assertNotIn('set-iam-policy',text)
        self.assertNotIn('--set-env-vars',text)
        self.assertNotIn('delete',text)

    def test_unknown_existing_service_fails_closed(self):
        with self.assertRaises(deploy.DeploymentError):deploy.deploy(self.c,IMAGE,self.runner([result(1,error='NOT_FOUND')]),lambda _:None)
        self.assertFalse(any('update' in c for c in self.calls))

    def test_unready_revision_never_passes(self):
        unready=ready();unready['status']['latestReadyRevisionName']='old'
        with self.assertRaises(deploy.DeploymentError):deploy.deploy(self.c,IMAGE,self.runner([result(data={'metadata':{}}),result(),result(data=unready)]),lambda _:None,polls=1)

    def test_competing_writer_image_is_detected(self):
        with self.assertRaises(deploy.DeploymentError):deploy.deploy(self.c,IMAGE,self.runner([result(data={'metadata':{}}),result(),result(data=ready('other-image'))]),lambda _:None)

    def test_mutable_or_wrong_repository_image_denied(self):
        for image in [ENV['CFP_IMAGE_REPOSITORY']+':latest','other/image@sha256:'+'b'*64]:
            with self.subTest(image=image),self.assertRaises(deploy.DeploymentError):deploy.deploy(self.c,image,self.runner([]),lambda _:None)

    def test_missing_image_metadata_fails_closed(self):
        value=ready();value['spec']['template']['spec']['containers']=[]
        with self.assertRaises(deploy.DeploymentError):deploy.deploy(self.c,IMAGE,self.runner([result(data={'metadata':{}}),result(),result(data=value)]),lambda _:None)

    def test_queue_compares_actual_timestamp_not_text(self):
        own=row('build-b','2026-10-05T01:00:00.1Z');old=row('build-a','2026-10-05T01:00:00Z')
        with self.assertRaises(deploy.DeploymentError):deploy.queue(self.c,self.runner([result(data=[own,old])]),lambda _:None,polls=1)

    def test_no_env_values_in_metadata_format(self):
        deploy.deploy(self.c,IMAGE,self.runner([result(data={'metadata':{}}),result(),result(data=ready())]),lambda _:None)
        formats=[a for c in self.calls for a in c if a.startswith('--format=')]
        self.assertTrue(all('containers)' not in f and 'env' not in f for f in formats))


if __name__=='__main__':unittest.main()
