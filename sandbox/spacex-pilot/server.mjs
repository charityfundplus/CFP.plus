import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const root = new URL('./', import.meta.url);
// Explicit asset allowlist; no proxy, upload, import endpoint or arbitrary filesystem path.
const assets = new Map([['/',['index.html','text/html; charset=utf-8']],['/registry.json',['registry.json','application/json']]]);
export async function handler(req,res) {
    res.setHeader('Content-Security-Policy',"default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'");
    res.setHeader('X-Content-Type-Options','nosniff');
    res.setHeader('Cache-Control','no-store');
    if (!['GET','HEAD'].includes(req.method)) { res.writeHead(405,{Allow:'GET, HEAD'}); return res.end('READ_ONLY'); }
    const asset = assets.get(req.url);
    if (!asset) { res.writeHead(404); return res.end('NOT_FOUND'); }
    try { const data = await readFile(new URL(asset[0],root)); res.writeHead(200,{'Content-Type':asset[1]}); res.end(req.method === 'HEAD' ? undefined : data); }
    catch {res.writeHead(500);res.end('ASSET_UNAVAILABLE');}
}
export function server() { return createServer(handler); }
if (process.argv[1] === fileURLToPath(import.meta.url)) server().listen(4173,'127.0.0.1',()=>console.log('Local pilot: http://127.0.0.1:4173 (read-only; not a public preview)'));
