const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function context(responses = []) {
  const calls = [];
  const elements = new Map();
  const ctx = vm.createContext({
    console, URL, setTimeout, clearTimeout, Blob, Uint8Array,
    location: {origin:'http://localhost', pathname:'/login.html', replace: () => {}},
    window: {addEventListener() {}},
    document: {addEventListener() {}, getElementById: id => elements.get(id) || null},
    localStorage: {getItem: () => JSON.stringify({id:1, role:'ADMIN'})},
    fetch: async (url, options) => {
      calls.push({url:String(url), options});
      return responses.shift() || {ok:false,status:401,json:async()=>({})};
    },
  });
  return {ctx,calls,elements};
}
const read = filename => fs.readFileSync(path.join('docs/assets/js', filename), 'utf8');

test('API uses same-origin sessions and mutation protection on multipart requests', async () => {
  const {ctx,calls} = context([{ok:true,json:async()=>({user:{name:'Tester'}})}, {ok:true,status:200}]);
  vm.runInContext(read('app.js'),ctx);
  await vm.runInContext("apiRequest('/api/upload/faces', {method:'POST', body:'multipart-placeholder'})",ctx);
  assert.equal(calls[1].options.credentials,'same-origin');
  assert.equal(calls[1].options.headers['X-HFG-Request'],'1');
  assert.equal(calls[1].options.headers['Content-Type'],undefined);
  await assert.rejects(vm.runInContext("apiRequest('https://other.test/api/residents')",ctx),/this server/);
  assert.equal(calls.length,2);
});

test('forged localStorage identity cannot authenticate the UI', async () => {
  const {ctx} = context();
  vm.runInContext(read('app.js'),ctx);
  vm.runInContext(read('auth.js'),ctx);
  await vm.runInContext('authReady',ctx);
  assert.equal(vm.runInContext('getAuthUser()',ctx),null);
});

test('resident rendering escapes markup and never places names in event handlers', async () => {
  const {ctx,elements} = context();
  const list={innerHTML:''}; elements.set('residents-list',list);
  vm.runInContext(read('app.js'),ctx);
  vm.runInContext("fetchResidents = async () => [{id:1, name:`<img src=x onerror=alert(1)>\"'`, role:'<script>bad</script>',face_count:1}]",ctx);
  vm.runInContext(read('akun.js'),ctx);
  await vm.runInContext('renderResidents()',ctx);
  assert.ok(!list.innerHTML.includes('<img'));
  assert.ok(!list.innerHTML.includes('<script>'));
  assert.ok(list.innerHTML.includes('&lt;img'));
  assert.ok(!list.innerHTML.includes('onclick='));
  assert.ok(list.innerHTML.includes('data-id="1"'));
});

test('all pages use local assets and contain no inline JavaScript under the CSP', () => {
  for (const file of fs.readdirSync('docs').filter(f => f.endsWith('.html'))) {
    const html=fs.readFileSync(path.join('docs',file),'utf8');
    assert.ok(!/<script[^>]*src=["']https?:/i.test(html),file);
    assert.ok(!/<script(?:\s[^>]*)?>\s*\S/i.test(html.replace(/<script[^>]*src=[^>]+><\/script>/g,'')),file);
    assert.ok(!/\son(?:click|submit|load)=/i.test(html),file);
    for (const [,asset] of html.matchAll(/(?:src|href)="(assets\/[^"?#]+)"/g)) {
      assert.ok(fs.existsSync(path.join('docs',asset)),`${file}: ${asset}`);
    }
  }
});

test('camera capture requires explicit user activation', () => {
  assert.ok(read('dashboard.js').includes("getElementById('start-camera-btn')?.addEventListener('click'"));
  assert.ok(read('scan.js').includes("getElementById('activate-scan-camera')?.addEventListener('click'"));
  assert.ok(!fs.readFileSync('docs/scan.html','utf8').includes('startWebcam('));
});
