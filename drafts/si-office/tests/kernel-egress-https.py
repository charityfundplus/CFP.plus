"""NEW kernel-meter/TLS-listener integration; no retained suites run."""
import importlib.util
import json
import socket
import ssl
import subprocess
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('kernel_guard',root/'scripts/kernel-egress-guard.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200);self.end_headers();self.wfile.write(b'synthetic TLS fixture')
    def log_message(self,*args):pass


class Checks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.dir=Path(self.tmp.name)
        self.state=self.dir/'meter-state.json';self.quote=self.dir/'quote.json'
        self.quote.write_text(json.dumps({'verified':True,'gross_monthly_cents':1342,'meter_at':int(time.time())}))
        self.guards=[];self.server=None;self.server_thread=None

    def tearDown(self):
        for g in self.guards:g.stop()
        if self.server and self.server_thread.is_alive():self.server.shutdown()
        if self.server:self.server.server_close();self.server_thread.join(2)
        self.tmp.cleanup()

    def tls(self):
        cert=self.dir/'cert.pem';key=self.dir/'key.pem'
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','1','-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost,IP:127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(cert,key);self.server.socket=context.wrap_socket(self.server.socket,server_side=True)
        self.address=self.server.server_address
        self.client_context=ssl.create_default_context(cafile=str(cert))
        self.server_thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.02},daemon=True);self.server_thread.start()

    def close_https(self):
        self.server.shutdown();self.server.server_close()

    def make_guard(self,**kw):
        g=module.KernelEgressGuard(self.state,self.quote,self.close_https,interval=.01)
        self.guards.append(g)
        self.assertTrue(g.arm(limit=kw.get('limit',10000000),expires=kw.get('expires',int(time.time())+30),approval=True))
        return g

    def closed_https(self,g):
        self.assertTrue(g.closed.wait(2),g.error)
        self.assertIsNone(g.error)
        with self.assertRaises(OSError):socket.create_connection(self.address,timeout=.2)

    def test_real_tls_traffic_is_seen_in_all_visible_kernel_counters(self):
        self.tls();g=self.make_guard()
        sample=module.kernel_sample();self.assertIn('lo',sample)
        with socket.create_connection(self.address,timeout=1) as raw:
            with self.client_context.wrap_socket(raw,server_hostname='localhost') as s:
                s.sendall(b'GET / HTTP/1.0\r\nHost: localhost\r\n\r\n')
                while s.recv(4096):pass
        for _ in range(100):
            value=json.loads(self.state.read_text())
            if value['used']>0:break
            time.sleep(.01)
        self.assertGreater(value['used'],0);self.assertEqual(set(value['last']),set(sample))

    def test_traffic_outside_proxy_triggers_actual_tls_listener_close(self):
        self.tls();g=self.make_guard(limit=8192)
        # Direct IPv4/IPv6 UDP bypasses application/proxy entirely; real kernel bytes.
        for family,address in [(socket.AF_INET,('127.0.0.1',9)),(socket.AF_INET6,('::1',9))]:
            with socket.socket(family,socket.SOCK_DGRAM) as s:
                for _ in range(8):s.sendto(b'x'*2048,address)
        self.closed_https(g);self.assertEqual(g.reason,'EGRESS_LIMIT')
        state=json.loads(self.state.read_text());self.assertEqual(state['status'],'CLOSED')
        fresh=module.KernelEgressGuard(self.state,self.quote,self.close_https)
        self.assertFalse(fresh.arm(limit=10000000,expires=int(time.time())+30,approval=True))

    def test_meter_missing_stops_actual_https_not_only_admission(self):
        self.tls();g=self.make_guard();self.quote.unlink()
        self.closed_https(g);self.assertEqual(g.reason,'METER_STATE_OR_QUOTE_INVALID')

    def test_budget_forecast_stops_actual_https(self):
        self.tls();g=self.make_guard()
        self.quote.write_text(json.dumps({'verified':True,'gross_monthly_cents':1501,'meter_at':int(time.time())}))
        self.closed_https(g);self.assertEqual(g.reason,'BUDGET_EXCEEDED')

    def test_expiry_stops_actual_https_without_request(self):
        self.tls();g=self.make_guard(expires=int(time.time())+1)
        self.closed_https(g);self.assertEqual(g.reason,'LEASE_EXPIRED')

    def test_missing_authority_never_arms(self):
        g=module.KernelEgressGuard(self.state,self.quote,lambda:None)
        self.assertFalse(g.arm(limit=10000,expires=int(time.time())+30))
        self.assertFalse(self.state.exists())


if __name__=='__main__':unittest.main(verbosity=2)
