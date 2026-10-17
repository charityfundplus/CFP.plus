import base64
import copy
import io
import json
import sqlite3
import sys
import time
import unittest
import urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from provider_notion import Blocked,Ledger,Notion,Provider,Transport,canonical,sha,verify_approval,NoRedirect
from run_provider_notion import run,verify_environment
from unittest.mock import patch

SOURCE='1'*32;PARENT='2'*32;CREATED='3'*32
TOKEN='synthetic-notion-token';KEY='synthetic-provider-key'
CONTEXT={'repository':'charityfundplus/CFP.plus','ref':'refs/heads/test','sha':'a'*40,'run_id':'123','run_attempt':'1'}

def blocks(value,**extra):
    return {'object':'list','results':[{'type':'paragraph','paragraph':{'rich_text':[{'plain_text':value}]}}], 'has_more':False,**extra}

class Fake:
    def __init__(self,*responses):self.responses=list(responses);self.calls=[]
    def request(self,*args):
        self.calls.append(args)
        value=self.responses.pop(0)
        if isinstance(value,Exception):raise value
        return copy.deepcopy(value)

class Response:
    def __init__(self,value):self.raw=json.dumps(value).encode()
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,size):return self.raw[:size]

class Opener:
    def __init__(self,*responses):self.responses=list(responses);self.calls=[]
    def open(self,*args,**kw):
        self.calls.append((args,kw));r=self.responses.pop(0)
        if isinstance(r,Exception):raise r
        return Response(r)

class TestAdapters(unittest.TestCase):
    def setUp(self):
        self.private=Ed25519PrivateKey.generate()
        self.pub=base64.b64encode(self.private.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode()
        self.transport=Fake({'object':'page','id':CREATED,'parent':{'page_id':PARENT}},blocks('Approved output'))
        self.notion=Notion(TOKEN,[SOURCE],PARENT,self.transport)
        self.plan=self.notion.plan('gemini','gemini-configured',SOURCE,'Approved output')
        self.ledger=Ledger(':memory:')
    def tearDown(self):self.ledger.close()
    def sign(self,plan=None,**changes):
        now=int(time.time());claims={'plan_sha256':sha(plan or self.plan),'context':CONTEXT,'issued_at':now-1,'expires_at':now+300,'nonce':'b'*32,'approver':'synthetic-reviewer','scope':'create-sandbox',**changes}
        return {'claims':claims,'signature':base64.b64encode(self.private.sign(canonical(claims))).decode()}
    def create(self,approval=None,plan=None):
        return self.notion.create_and_readback(plan or self.plan,approval if approval is not None else self.sign(),CONTEXT,self.pub,self.ledger)
    def test_create_private_child_and_exact_readback(self):
        receipt=self.create();self.assertEqual(receipt['readback'],'PASS');self.assertFalse(receipt['officialDocumentsWritten'])
        self.assertEqual(self.transport.calls[0][1],'https://api.notion.com/v1/pages');self.assertEqual(self.transport.calls[0][3]['parent']['page_id'],PARENT)
        self.assertNotIn(TOKEN,json.dumps(receipt));self.assertNotIn('Approved output',json.dumps(receipt));self.assertNotIn(CREATED,json.dumps(receipt))
    def test_missing_approval_zero_calls(self):
        with self.assertRaises(Blocked):self.create({})
        self.assertFalse(self.transport.calls)
    def test_unsigned_boolean_does_not_authorize(self):
        with self.assertRaises(Blocked):self.create({'approved':True})
        self.assertFalse(self.transport.calls)
    def test_invalid_signature_zero_calls(self):
        a=self.sign();a['signature']='invalid'
        with self.assertRaises(Blocked):self.create(a)
        self.assertFalse(self.transport.calls)
    def test_changed_text_denied_before_network(self):
        approval=self.sign();plan={**self.plan,'text':'Modified'}
        with self.assertRaises(Blocked):self.create(approval,plan)
        self.assertFalse(self.transport.calls)
    def test_changed_target_denied(self):
        with self.assertRaises(Blocked):self.create(self.sign(),{**self.plan,'sandbox_parent':SOURCE})
        self.assertFalse(self.transport.calls)
    def test_official_append_action_denied(self):
        plan={**self.plan,'action':'append-official'}
        with self.assertRaises(Blocked):self.create(self.sign(plan),plan)
        self.assertFalse(self.transport.calls)
    def test_expired_and_future_approval_denied(self):
        now=int(time.time())
        for a in [self.sign(expires_at=now-1),self.sign(issued_at=now+10)]:
            with self.assertRaises(Blocked):self.create(a)
        self.assertFalse(self.transport.calls)
    def test_wrong_run_attempt_provider_and_source_sha_denied(self):
        for context in [{**CONTEXT,'run_attempt':'2'},{**CONTEXT,'sha':'c'*40}]:
            with self.assertRaises(Blocked):self.create(self.sign(context=context))
        with self.assertRaises(Blocked):self.create(self.sign(),{**self.plan,'provider':'meta'})
        self.assertFalse(self.transport.calls)
    def test_wrong_public_key_denied(self):
        with self.assertRaises(Blocked):verify_approval(self.sign(),self.plan,CONTEXT,'bad')
    def test_replay_denied(self):
        a=self.sign();self.create(a)
        with self.assertRaisesRegex(Blocked,'REPLAY'):self.create(a)
        self.assertEqual(len(self.transport.calls),2)
    def test_uncertain_post_consumes_nonce_and_does_not_retry(self):
        self.transport.responses=[Blocked('POST_UNCERTAIN_NO_RETRY')];a=self.sign()
        with self.assertRaises(Blocked):self.create(a)
        with self.assertRaisesRegex(Blocked,'REPLAY'):self.create(a)
        self.assertEqual(len(self.transport.calls),1)
    def test_readback_mismatch_not_pass(self):
        self.transport.responses[1]=blocks('Different')
        with self.assertRaisesRegex(Blocked,'READBACK'):self.create()
    def test_returned_parent_must_match(self):
        self.transport.responses[0]['parent']['page_id']=SOURCE
        with self.assertRaisesRegex(Blocked,'CREATE_RESPONSE'):self.create()
        self.assertEqual(len(self.transport.calls),1)
    def test_acl_denies_before_read(self):
        with self.assertRaisesRegex(Blocked,'SCOPE_DENIED'):self.notion.read(PARENT)
        self.assertFalse(self.transport.calls)
    def test_unsupported_or_nested_blocks_do_not_silently_disappear(self):
        for block in [{'type':'table'},{'type':'paragraph','has_children':True}]:
            f=Fake({'object':'list','results':[block],'has_more':False})
            with self.assertRaisesRegex(Blocked,'UNSUPPORTED_SOURCE_BLOCK'):Notion(TOKEN,[SOURCE],PARENT,f).read(SOURCE)
    def test_read_pagination(self):
        f=Fake(blocks('first',has_more=True,next_cursor='next'),blocks('second'));n=Notion(TOKEN,[SOURCE],PARENT,f)
        self.assertEqual(n.read(SOURCE),'first\nsecond');self.assertIn('start_cursor=next',f.calls[1][1])
    def test_gemini_header_and_response_contract(self):
        f=Fake({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'Private draft'}]}}]})
        self.assertEqual(Provider('gemini','configured-model',KEY,f).generate('Input'),'Private draft')
        self.assertNotIn(KEY,f.calls[0][1]);self.assertEqual(f.calls[0][2]['x-goog-api-key'],KEY)
    def test_meta_fixed_api_and_no_arbitrary_base_url(self):
        f=Fake({'choices':[{'finish_reason':'stop','message':{'content':'Private draft'}}]})
        self.assertEqual(Provider('meta','licensed-model',KEY,f).generate('Input'),'Private draft');self.assertEqual(f.calls[0][1],'https://api.meta.ai/v1/chat/completions')
    def test_provider_errors_and_incomplete_output_not_success(self):
        for provider,response in [('gemini',{'candidates':[]}),('meta',{'choices':[{'finish_reason':'length','message':{'content':'x'}}]})]:
            with self.assertRaises(Blocked):Provider(provider,'model',KEY,Fake(response)).generate('Input')
    def test_provider_secret_echo_is_blocked(self):
        f=Fake({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':KEY}]}}]})
        with self.assertRaisesRegex(Blocked,'SECRET_ECHO'):Provider('gemini','model',KEY,f).generate('Input')
        with self.assertRaisesRegex(Blocked,'SECRET_ECHO'):self.notion.plan('gemini','model',SOURCE,TOKEN)
    def test_model_path_injection_denied(self):
        for value in ['../model','bad?key=leak','model\nheader']:
            with self.assertRaises(Blocked):Provider('gemini',value,KEY,Fake())
    def test_401_403_not_retried_or_leaked(self):
        for status in [401,403]:
            f=Opener(urllib.error.HTTPError('https://api.notion.com/v1/pages',status,'SENSITIVE SERVER MESSAGE',{},io.BytesIO(b'PRIVATE BODY')))
            with self.assertRaises(Blocked) as cm:Transport(f).request('POST','https://api.notion.com/v1/pages',{'Authorization':'Bearer '+TOKEN},{})
            self.assertEqual(len(f.calls),1);self.assertNotIn('SENSITIVE',str(cm.exception));self.assertNotIn(TOKEN,str(cm.exception))
    def test_get_retries_are_bounded(self):
        error=lambda:urllib.error.HTTPError('https://api.notion.com/v1/pages',429,'private',{},None)
        f=Opener(error(),error(),{'object':'page'});wait=[]
        self.assertEqual(Transport(f,wait.append).request('GET','https://api.notion.com/v1/pages',{}),{'object':'page'});self.assertEqual(wait,[1,2])
    def test_post_timeout_not_retried(self):
        f=Opener(urllib.error.URLError('sensitive '+TOKEN))
        with self.assertRaisesRegex(Blocked,'POST_UNCERTAIN'):Transport(f).request('POST','https://api.notion.com/v1/pages',{}, {})
        self.assertEqual(len(f.calls),1)
    def test_redirects_denied_and_secret_endpoint_rejected(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,'',{},'https://attacker.invalid'))
        for url in ['http://api.notion.com/v1/pages','https://attacker.invalid/v1','https://api.meta.ai.evil/v1','https://api.meta.ai/v1?key=bad']:
            with self.assertRaises(Blocked):Transport(Opener()).request('POST',url,{},{})
    def test_response_size_bound(self):
        f=Opener({'secret':'x'*270000})
        with self.assertRaisesRegex(Blocked,'TOO_LARGE'):Transport(f).request('GET','https://api.notion.com/v1/pages',{})
    def test_draft_uses_read_only_source_and_no_write(self):
        f=Fake(blocks('Approved source'),{'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'Draft text'}]}}]})
        env={'CMP_NOTION_TOKEN':TOKEN,'CMP_NOTION_READABLE_PAGE_IDS':json.dumps([SOURCE]),'CMP_NOTION_SANDBOX_PARENT':PARENT,'CMP_NOTION_SOURCE_PAGE':SOURCE,'GEMINI_MODEL':'configured','GEMINI_API_KEY':KEY}
        receipt=run('gemini','draft',env,f);self.assertEqual(receipt['create'],'NOT_TESTED');self.assertNotIn('Draft text',json.dumps(receipt));self.assertEqual([c[0] for c in f.calls],['GET','POST'])
    def test_create_runner_never_calls_provider_or_changes_approved_text(self):
        env={'CMP_NOTION_TOKEN':TOKEN,'CMP_NOTION_READABLE_PAGE_IDS':json.dumps([SOURCE]),'CMP_NOTION_SANDBOX_PARENT':PARENT,'CMP_NOTION_SOURCE_PAGE':SOURCE,'GEMINI_MODEL':'gemini-configured','CMP_APPROVED_TEXT':'Approved output','CMP_NOTION_APPROVAL_JSON':json.dumps(self.sign()),'CMP_APPROVAL_PUBLIC_KEY':self.pub,'CMP_APPROVAL_LEDGER_PATH':':memory:'}
        env.update({v:CONTEXT[k] for k,v in {'repository':'GITHUB_REPOSITORY','ref':'GITHUB_REF','sha':'GITHUB_SHA','run_id':'GITHUB_RUN_ID','run_attempt':'GITHUB_RUN_ATTEMPT'}.items()})
        result=run('gemini','create-sandbox',env,self.transport);self.assertEqual(result['readback'],'PASS');self.assertTrue(all('api.notion.com' in c[1] for c in self.transport.calls))
    def test_environment_missing_or_unprotected_denied(self):
        with self.assertRaises(Blocked):verify_environment({})
        with patch('urllib.request.build_opener',return_value=Opener({'protection_rules':[]})):
            with self.assertRaisesRegex(Blocked,'REVIEWERS_UNVERIFIED'):verify_environment({'GITHUB_REPOSITORY':'charityfundplus/CFP.plus','CMP_APPROVAL_ENVIRONMENT':'existing','GITHUB_TOKEN':'synthetic'})
    def test_workflows_have_no_secret_shell_interpolation_or_raw_artifacts(self):
        root=Path(__file__).resolve().parents[3]
        for name in ['cmp-gemini-notion-pilot.yml','cmp-meta-content-pilot.yml']:
            content=(root/'.github/workflows'/name).read_text()
            self.assertNotIn('repository_dispatch:',content);self.assertIn('environment:',content)
            self.assertNotIn('?key=',content);self.assertNotIn('gemini-response.json',content);self.assertNotIn('meta-response.json',content)
            self.assertIn('path: cmp-evidence.json',content)
            for line in content.splitlines():
                if 'run:' in line:self.assertNotIn('${{ secrets.',line)

if __name__=='__main__':unittest.main(verbosity=2)
