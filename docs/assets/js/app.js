// frontend/assets/js/app.js

// ====================================================================
// API BASE (Render) — PASTIKAN TANPA TRAILING SLASH
// ====================================================================
const API_BASE = '/api';
const MOCK_API_BASE = API_BASE;

let residents = [];
let logs = [];

/**
 * Helper fetch JSON + error handling rapi
 */
async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path.startsWith('/') ? '' : '/'}${path}`;

  const res = await apiRequest(url, {
    ...options,
    headers: {
      ...(options.headers || {}),
    },
  });

  // coba parse json kalau ada body
  let data = null;
  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try {
      data = await res.json();
    } catch (_) {
      data = null;
    }
  } else {
    // fallback text (opsional)
    try {
      data = await res.text();
    } catch (_) {
      data = null;
    }
  }

  if (!res.ok) {
    const msg =
      (data && data.message) ||
      (typeof data === 'string' && data) ||
      `Request failed (Status: ${res.status})`;
    throw new Error(msg);
  }

  return data;
}

/**
 * Mengambil data Penghuni dari Backend
 * Endpoint: GET /api/residents
 */
async function fetchResidents() {
  console.log("API: Fetching /api/residents...");

  try {
    const data = await apiFetch('/residents');
    return Array.isArray(data) ? data : [];
  } catch (error) {
    console.error("Error fetching residents:", error);
    return [];
  }
}

/**
 * Mengambil data Log dari Backend
 * Endpoint: GET /api/logs?limit=200
 */
async function fetchLogs() {
  console.log("API: Fetching /api/logs...");

  try {
    const data = await apiFetch('/logs?limit=200');

    // Normalisasi timestamp agar konsisten dipakai di UI (Date object)
    const parsed = (data || []).map(item => {
      let ts = item.timestamp;
      let dateObj = null;

      if (typeof ts === 'string' && ts.includes(' ')) {
        // Format SQLite default: "YYYY-MM-DD HH:MM:SS"
        const [dPart, tPart] = ts.split(' ');
        const [y, m, d] = dPart.split('-').map(Number);
        const [hh, mm, ss] = tPart.split(':').map(Number);
        dateObj = new Date(y, (m - 1), d, hh, mm, ss || 0);
      } else {
        const tmp = new Date(ts);
        dateObj = isNaN(tmp.getTime()) ? new Date() : tmp;
      }

      return { ...item, timestamp: dateObj };
    });

    return parsed;

  } catch (error) {
    console.error("Error fetching logs:", error);
    return [];
  }
}

/**
 * Menambahkan Penghuni Baru ke database
 * Endpoint: POST /api/residents
 */
async function addResidentToBackend(residentData) {


  try {
    const data = await apiFetch('/residents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(residentData),
    });

    return data;

  } catch (error) {
    console.error("Error saving resident metadata:", error);
    throw new Error(error.message || 'Gagal menyimpan metadata penghuni.');
  }
}

/**
 * Memeriksa apakah data wajah untuk nama tertentu sudah ada di folder dataset.
 * Endpoint (kemungkinan): GET /api/check_dataset/<name>
 */
async function checkDatasetExistence(name) {
  if (!name) return { exists: false, face_count: 0 };


  try {
    const data = await apiFetch(`/check_dataset/${encodeURIComponent(name)}`);

    // pastikan bentuknya konsisten
    if (data && typeof data.exists === 'boolean') return data;
    return { exists: false, face_count: 0 };

  } catch (error) {
    console.error("Error fetching or parsing dataset check:", error);
    return { exists: false, face_count: 0 };
  }
}

/**
 * Mengubah Data URL (Base64) menjadi objek Blob
 */
function dataURLtoBlob(dataurl) {
  const arr = dataurl.split(',');
  const mime = arr[0].match(/:(.*?);/)[1];
  const bstr = atob(arr[1]);

  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) u8arr[n] = bstr.charCodeAt(n);

  return new Blob([u8arr], { type: mime });
}


let sessionUser = null;
const authReady = fetch('/api/auth/me', {credentials: 'same-origin', cache: 'no-store'})
  .then(async res => { sessionUser = res.ok ? (await res.json()).user : null; })
  .catch(() => { sessionUser = null; });

async function apiRequest(url, options = {}) {
  await authReady;
  const target = new URL(url, location.origin);
  if (target.origin !== location.origin || !target.pathname.startsWith('/api/')) {
    throw new Error('API requests must stay on this server');
  }
  const res = await fetch(target, {
    ...options,
    credentials: 'same-origin',
    headers: {...options.headers, 'X-HFG-Request': '1'},
  });
  if (res.status === 401 && !target.pathname.endsWith('/auth/login')) {
    sessionUser = null;
    if (!location.pathname.includes('login')) location.replace('/login.html');
  }
  return res;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
}
