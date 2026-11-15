import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {verifyRelease} from '../sandbox/release-control.mjs';
import {registrySourceFromEnvironment} from '../core/registry-read-model.mjs';

// CLI and integration tests use this same loopback launcher. Registry data stays
// in its existing checkout; the release contains no new master data.
export async function serveActiveRelease({directory, database, port = 4174, previewOrigin = null, registrySource}) {
  if (!directory) throw Error('CFP_P2_RELEASE_DIR_REQUIRED');
  const active = JSON.parse(readFileSync(join(directory, 'active.json')));
  verifyRelease(active.release, active.digest);
  const {P2Sandbox} = await import(pathToFileURL(join(active.release, 'sandbox/p2-service.mjs')));
  const {createP2HTTP} = await import(pathToFileURL(join(active.release, 'sandbox/p2-http.mjs')));
  const path = active.database || database;
  if (!path) throw Error('CFP_P2_DB_REQUIRED');
  const service = new P2Sandbox(path, {registrySource});
  const server = createP2HTTP({service, previewOrigin});
  try {
    await new Promise((done, reject) => { server.once('error', reject); server.listen(port, '127.0.0.1', done); });
    return {server, service, release: active.release, digest: active.digest};
  } catch (error) { service.close(); throw error; }
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const {server, service} = await serveActiveRelease({directory: process.env.CFP_P2_RELEASE_DIR,
    database: process.env.CFP_P2_DB, port: Number(process.env.CFP_P2_PORT || 4174),
    previewOrigin: process.env.CFP_P2_PREVIEW_ORIGIN || null, registrySource: registrySourceFromEnvironment()});
  process.on('SIGTERM', () => server.close(() => { service.close(); process.exit(0); }));
}
