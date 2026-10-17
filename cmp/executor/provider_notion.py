"""Issue #148 adapters on the existing outbound executor. No HTTP server.

The public receipt is an allowlist of codes/digests; input, generated output,
credentials, raw responses and exception messages never enter it.
"""
from __future__ import annotations
import base64
import hashlib
import json
import re
import sqlite3
import time
from urllib.parse import urlsplit
import urllib.request
import urllib.error
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


class Blocked(Exception):
    """Only controlled codes, never raw server/credential values."""
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def uuid(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-fA-F0-9]{32}|[a-fA-F0-9]{8}(-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}', value):
        raise Blocked('PAGE_ID_INVALID')
    return value.replace('-', '').lower()


def text(value, maximum=1800):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise Blocked('TEXT_INVALID_OR_TOO_LARGE')
    return value


def model_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,159}', value) or '..' in value:
        raise Blocked('MODEL_REQUIRED')
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Transport:
    """Fixed HTTPS origins, no redirects, bounded GET retries; POST never retries.

    Retains standard proxy and CA handling. Never exposes raw errors/responses.
    """
    def __init__(self, opener=None, sleeper=time.sleep):
        self.opener = opener or urllib.request.build_opener(NoRedirect())
        self.sleep = sleeper

    def request(self, method, url, headers, body=None):
        parsed = urlsplit(url)
        if method not in {'GET','POST'} or parsed.scheme != 'https' or parsed.netloc not in {'api.notion.com','generativelanguage.googleapis.com','api.meta.ai'} or (parsed.query and parsed.hostname != 'api.notion.com') or parsed.username or parsed.password or parsed.fragment:
            raise Blocked('ENDPOINT_DENIED')
        attempts = 3 if method == 'GET' else 1
        for attempt in range(attempts):
            request = urllib.request.Request(url, data=None if body is None else canonical(body), headers=headers, method=method)
            try:
                with self.opener.open(request, timeout=25) as response:
                    raw = response.read(262145)
                    if len(raw)>262144: raise Blocked('RESPONSE_TOO_LARGE')
                    try: value=json.loads(raw)
                    except (ValueError,UnicodeError): raise Blocked('RESPONSE_INVALID') from None
                    if not isinstance(value,dict): raise Blocked('RESPONSE_INVALID')
                    return value
            except urllib.error.HTTPError as error:
                status=error.code
                error.close()
                if status in (429,502,503,504) and attempt+1<attempts:
                    self.sleep(min(2**attempt,4));continue
                if status==401: raise Blocked('AUTH_401') from None
                if status==403: raise Blocked('ACCESS_403') from None
                if status==429: raise Blocked('RATE_LIMIT_429') from None
                raise Blocked('HTTP_'+str(status) if method=='GET' else 'POST_FAILED_OR_UNCERTAIN_NO_RETRY') from None
            except (urllib.error.URLError,OSError,TimeoutError):
                raise Blocked('NETWORK_ERROR' if method=='GET' else 'POST_UNCERTAIN_NO_RETRY') from None
        raise Blocked('REQUEST_FAILED')


def credential(value):
    if not isinstance(value, str) or not value or '\r' in value or '\n' in value:
        raise Blocked('CREDENTIAL_MISSING_OR_INVALID')
    return value


class Provider:
    def __init__(self, provider, model, key, transport):
        if provider not in {'gemini', 'meta'}: raise Blocked('PROVIDER_DENIED')
        self.provider, self.model = provider, model_name(model)
        self._key, self.transport = credential(key), transport

    def generate(self, prompt):
        text(prompt, 16000)
        if self.provider == 'gemini':
            # Gemini API generateContent, not Gemini consumer login/Vertex auth.
            if '/' in self.model: raise Blocked('MODEL_REQUIRED')
            value = self.transport.request('POST', 'https://generativelanguage.googleapis.com/v1beta/models/' + self.model + ':generateContent',
                {'Content-Type': 'application/json', 'x-goog-api-key': self._key},
                {'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {'maxOutputTokens': 512}})
            try:
                candidate = value['candidates'][0]
                if candidate.get('finishReason') != 'STOP': raise Blocked('PROVIDER_OUTPUT_INCOMPLETE')
                output = ''.join(p.get('text', '') for p in candidate['content']['parts'] if not p.get('thought'))
            except (KeyError, IndexError, TypeError): raise Blocked('PROVIDER_RESPONSE_INVALID') from None
        else:
            # Meta Model API OpenAI-compatible surface, not Meta AI consumer UI.
            value = self.transport.request('POST', 'https://api.meta.ai/v1/chat/completions',
                {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self._key},
                {'model': self.model, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 512, 'stream': False})
            try:
                choice = value['choices'][0]
                if choice.get('finish_reason') != 'stop': raise Blocked('PROVIDER_OUTPUT_INCOMPLETE')
                output = choice['message']['content']
            except (KeyError, IndexError, TypeError): raise Blocked('PROVIDER_RESPONSE_INVALID') from None
        output = text(output)
        # A model echoing its key must not feed it into Notion or evidence.
        if self._key in output: raise Blocked('SECRET_ECHO_BLOCKED')
        return output


class Notion:
    def __init__(self, token, readable_pages, sandbox_parent, transport):
        self._token = credential(token)
        self.readable = {uuid(p) for p in readable_pages}
        self.parent = uuid(sandbox_parent)
        self.transport = transport

    def _request(self, method, path, body=None):
        return self.transport.request(method, 'https://api.notion.com/v1/' + path,
            {'Authorization': 'Bearer ' + self._token, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json'}, body)

    def read(self, page):
        page = uuid(page)
        if page not in self.readable: raise Blocked('READ_SCOPE_DENIED')
        blocks, cursor = [], None
        for _ in range(10):
            path = 'blocks/' + page + '/children?page_size=100'
            if cursor:
                if not re.fullmatch(r'[A-Za-z0-9_-]{1,200}', cursor): raise Blocked('CURSOR_INVALID')
                path += '&start_cursor=' + cursor
            value = self._request('GET', path)
            if value.get('object') != 'list' or not isinstance(value.get('results'), list): raise Blocked('NOTION_RESPONSE_INVALID')
            for b in value['results']:
                if not isinstance(b, dict): raise Blocked('NOTION_RESPONSE_INVALID')
                kind = b.get('type')
                if b.get('has_children') or kind not in {'paragraph','heading_1','heading_2','heading_3'}:
                    raise Blocked('UNSUPPORTED_SOURCE_BLOCK')
                if kind in {'paragraph', 'heading_1', 'heading_2', 'heading_3'}:
                    parts = b.get(kind, {}).get('rich_text', [])
                    blocks.append(''.join(p.get('plain_text', p.get('text', {}).get('content', '')) for p in parts))
            if value.get('has_more') is False: return '\n'.join(blocks)
            if value.get('has_more') is not True or not value.get('next_cursor'): raise Blocked('NOTION_RESPONSE_INVALID')
            cursor = value['next_cursor']
        raise Blocked('READ_PAGINATION_LIMIT')

    def plan(self, provider, model, source_page, approved_text):
        if provider not in {'gemini', 'meta'}: raise Blocked('PROVIDER_DENIED')
        source_page = uuid(source_page)
        if source_page not in self.readable: raise Blocked('READ_SCOPE_DENIED')
        approved_text = text(approved_text)
        if self._token in approved_text: raise Blocked('SECRET_ECHO_BLOCKED')
        return {'contract': 'cmp-provider-notion/v1', 'action': 'create-sandbox', 'provider': provider,
            'model': model_name(model), 'source_page': source_page, 'sandbox_parent': self.parent,
            'text': approved_text, 'title': 'CFP+ integration sandbox receipt'}

    def create_and_readback(self, plan, approval, context, public_key, ledger, receipt=None):
        # Rebuild the entire plan against server-owned ACL: HTTP/provider output cannot select a parent.
        expected = self.plan(plan.get('provider'), plan.get('model'), plan.get('source_page'), plan.get('text'))
        if expected != plan: raise Blocked('PLAN_MISMATCH')
        verify_approval(approval, expected, context, public_key)
        # Consume BEFORE POST. Failed/uncertain writes are not automatically replayed.
        ledger.consume(approval['claims']['nonce'])
        payload = {'parent': {'type': 'page_id', 'page_id': self.parent},
            'properties': {'title': {'type': 'title', 'title': [{'type': 'text', 'text': {'content': plan['title']}}]}},
            'children': [{'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': plan['text']}}]}}]}
        if receipt is not None: receipt['create']='ATTEMPTED_OUTCOME_UNKNOWN'
        result = self._request('POST', 'pages', payload)
        try:
            created = uuid(result['id'])
            if result['object'] != 'page' or uuid(result['parent']['page_id']) != self.parent: raise Blocked('CREATE_RESPONSE_INVALID')
        except (KeyError, TypeError): raise Blocked('CREATE_RESPONSE_INVALID') from None
        if created == self.parent or created in self.readable: raise Blocked('CREATE_RESPONSE_INVALID')
        # Only the exact freshly created child is admitted to readback; no ACL expansion in Notion.
        if receipt is not None: receipt['create']='PASS'
        self.readable.add(created)
        observed = self.read(created)
        if observed != plan['text']: raise Blocked('READBACK_MISMATCH')
        if receipt is not None: receipt['readback']='PASS'
        return {'provider': plan['provider'], 'read': 'NOT_TESTED', 'create': 'PASS', 'readback': 'PASS',
            'plan_sha256': sha(plan), 'output_sha256': sha(plan['text']), 'created_page_sha256': sha(created),
            'activationAllowed': False, 'officialDocumentsWritten': False}


class Ledger:
    def __init__(self, path):
        try:
            self.db = sqlite3.connect(path)
            self.db.execute('CREATE TABLE IF NOT EXISTS consumed(nonce TEXT PRIMARY KEY)')
            self.db.commit()
        except sqlite3.Error: raise Blocked('LEDGER_UNAVAILABLE') from None

    def consume(self, nonce):
        try:
            self.db.execute('INSERT INTO consumed VALUES(?)', (nonce,))
            self.db.commit()
        except sqlite3.IntegrityError: raise Blocked('APPROVAL_REPLAY_DENIED') from None
        except sqlite3.Error: raise Blocked('LEDGER_UNAVAILABLE') from None

    def close(self): self.db.close()


def verify_approval(envelope, plan, context, public_key, now=None):
    """External human issuer owns private Ed25519 key; executor has public key only.

    Public context is bound to repo/ref/SHA/provider/action/run_id/run_attempt.
    No boolean or caller-supplied role can authorize a write.
    """
    try:
        if set(envelope) != {'claims', 'signature'}: raise ValueError()
        claims = envelope['claims']
        required = {'plan_sha256', 'context', 'issued_at', 'expires_at', 'nonce', 'approver', 'scope'}
        if set(claims) != required or claims['scope'] != 'create-sandbox': raise ValueError()
        if claims['plan_sha256'] != sha(plan) or claims['context'] != context: raise ValueError()
        if not isinstance(context, dict) or set(context) != {'repository','ref','sha','run_id','run_attempt'}: raise ValueError()
        if context['repository'] != 'charityfundplus/CFP.plus' or not re.fullmatch(r'[a-f0-9]{40}', context['sha']): raise ValueError()
        if not context['ref'].startswith('refs/heads/') or not str(context['run_id']).isdigit() or not str(context['run_attempt']).isdigit(): raise ValueError()
        current = int(time.time()) if now is None else now
        issued, expires = claims['issued_at'], claims['expires_at']
        if type(issued) is not int or type(expires) is not int or not issued <= current < expires or expires-issued > 900: raise ValueError()
        if not re.fullmatch(r'[a-f0-9]{32}', claims['nonce']) or not re.fullmatch(r'[A-Za-z0-9_.@-]{1,100}', claims['approver']): raise ValueError()
        key = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key, validate=True))
        key.verify(base64.b64decode(envelope['signature'], validate=True), canonical(claims))
    except Exception:
        raise Blocked('APPROVAL_INVALID_OR_MISSING') from None
