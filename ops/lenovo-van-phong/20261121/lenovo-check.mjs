// CFP+ • HUB 69 • Chẩn đoán Văn Phòng Siêu Bộ Đôi trên Lenovo (chỉ đọc, không cần thư viện ngoài).
// Chạy trên Lenovo, Node.js 22+, trong khi `npm start` (drafts/si-office) đang chạy ở cửa sổ khác:
//   node lenovo-check.mjs <đường dẫn tới drafts/si-office>
// Không in secrets, không gửi dữ liệu ra ngoài máy; chỉ gọi 127.0.0.1 / localhost / [::1].
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import http from 'node:http';

const dir = path.resolve(process.argv[2] || '.');
const out = {platform: process.platform, node: process.version, dir, probes: [], manifest: null, proxyEnv: {}};

for (const k of ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'no_proxy'])
  if (process.env[k]) out.proxyEnv[k] = 'SET (giá trị ẩn)';

function probe(host, hostHeader) {
  return new Promise(res => {
    const r = http.get({host, port: 4173, path: '/', headers: {Host: hostHeader}, timeout: 4000}, resp => {
      let body = ''; resp.on('data', c => { if (body.length < 400) body += c; });
      resp.on('end', () => res({host, hostHeader, status: resp.statusCode, title: (body.match(/<title>([^<]*)/) || [])[1] || body.slice(0, 80)}));
    });
    r.on('timeout', () => { r.destroy(); res({host, hostHeader, error: 'TIMEOUT'}); });
    r.on('error', e => res({host, hostHeader, error: e.code || String(e)}));
  });
}
out.probes.push(await probe('127.0.0.1', '127.0.0.1:4173'));
out.probes.push(await probe('127.0.0.1', 'localhost:4173'));
out.probes.push(await probe('::1', '[::1]:4173'));

try {
  const name = 'ROUND1_CURRENT_MANIFEST';
  const raw = await readFile(path.join(dir, 'docs', name + '.json'));
  const expected = (await readFile(path.join(dir, 'docs', name + '.sha256'), 'utf8')).trim().split(/\s+/)[0];
  const self = createHash('sha256').update(raw).digest('hex');
  const m = JSON.parse(raw);
  const drift = [];
  for (const f of m.files) {
    let b; try { b = await readFile(path.join(dir, f.path)); } catch { drift.push({path: f.path, reason: 'MISSING'}); continue; }
    if (createHash('sha256').update(b).digest('hex') === f.sha256) continue;
    const lf = Buffer.from(b.toString('binary').replace(/\r\n/g, '\n'), 'binary');
    drift.push({path: f.path, reason: createHash('sha256').update(lf).digest('hex') === f.sha256 ? 'CRLF (git autocrlf trên Windows)' : 'NỘI DUNG KHÁC (commit sau manifest)'});
  }
  out.manifest = {name, selfChecksumOk: self === expected, selfCrlf: raw.includes('\r\n'), files: m.files.length, drift};
} catch (e) { out.manifest = {error: String(e.message || e)}; }

const p = out.probes[0];
out.verdict = p.status === 200 ? 'SERVER OK tại http://127.0.0.1:4173/ → nếu Chrome vẫn không mở: kiểm tra proxy/extension của Chrome (xem REPORT_VI.md mục 4)'
  : p.error === 'ECONNREFUSED' ? 'KHÔNG CÓ SERVER trên 127.0.0.1:4173 → chạy `npm start` trong drafts/si-office (Node 22+)'
  : p.status === 403 ? 'SERVER TỪ CHỐI Host → mở đúng http://127.0.0.1:4173/ (không dùng tên máy/IP LAN)'
  : 'XEM probes';
console.log(JSON.stringify(out, null, 1));
