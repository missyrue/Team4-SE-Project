/* Shared helpers used by every screen.
 *   App            global state (login token, role, registered screens)
 *   api()          fetch wrapper that talks to the REST API and throws readable errors
 *   el()           builds DOM nodes SAFELY (text is never parsed as HTML -> no XSS, OBS-SR-005)
 *   show()         switches screen
 */
const App = { token: null, role: null, name: null, views: {} };
try {
  App.token = localStorage.getItem('token');
  App.role = localStorage.getItem('role');
  App.name = localStorage.getItem('name');
} catch (e) { /* storage blocked: user simply has to log in again */ }

function saveSession(token, role, name) {
  App.token = token; App.role = role; App.name = name;
  try { localStorage.setItem('token', token); localStorage.setItem('role', role); localStorage.setItem('name', name); } catch (e) {}
}
function clearSession() {
  App.token = App.role = App.name = null;
  try { localStorage.removeItem('token'); localStorage.removeItem('role'); localStorage.removeItem('name'); } catch (e) {}
}

async function api(path, { method = 'GET', body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth && App.token) headers['Authorization'] = 'Bearer ' + App.token;   // auth:false = machine-to-machine call (payment gateway)
  const res = await fetch(path, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  if (res.status === 204) return null;            // "no content" (e.g. search with no matches)
  let data = null;
  try { data = await res.json(); } catch (e) { /* no body */ }
  if (!res.ok) {
    if (res.status === 401 && auth && App.token) {        // session expired or logged out elsewhere
      clearSession(); renderNav(); show('auth');
    }
    throw new Error((data && data.message) || res.statusText || 'Request failed');
  }
  return data;
}

function el(tag, props, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props || {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key === 'class') node.className = value;
    else if (key.startsWith('on') && typeof value === 'function') node.addEventListener(key.slice(2).toLowerCase(), value);
    else if (key === 'value') node.value = value;
    else node.setAttribute(key, value === true ? '' : value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child);                           // strings become text nodes, never HTML
  }
  return node;
}

function money(n) { return '₹' + Number(n).toFixed(2); }

function field(labelText, input) { return el('div', { class: 'field' }, el('label', {}, labelText), input); }

function table(headers, rows) {
  return el('div', { class: 'table-wrap' },
    el('table', {},
      el('thead', {}, el('tr', {}, headers.map(h => el('th', {}, h)))),
      el('tbody', {}, rows)));
}

function toast(message, isError = false) {
  const t = document.getElementById('toast');
  t.textContent = message;
  t.className = 'show' + (isError ? ' error' : '');
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => { t.className = ''; }, 3500);
}

async function addToCart(bookId, quantity = 1) {
  if (!App.token) { toast('Please log in to add books to your cart', true); show('auth'); return false; }
  try {
    await api('/api/cart/items', { method: 'POST', body: { bookId, quantity } });
    toast('Added to cart');
    renderNav();
    return true;
  } catch (e) { toast(e.message, true); return false; }
}

function show(view) {
  document.querySelectorAll('main > section').forEach(s => { s.hidden = s.id !== 'view-' + view; });
  document.querySelectorAll('nav button[data-view]').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  const render = App.views[view];
  if (render) render(document.getElementById('view-' + view));
}

function renderNav() {
  const nav = document.getElementById('nav');
  const link = (label, view) => el('button', { 'data-view': view, onclick: () => show(view) }, label);
  const items = [link('Catalogue', 'catalogue')];
  if (App.token && App.role === 'customer') items.push(link('Cart', 'cart'), link('My orders', 'orders'));
  if (App.token && App.role === 'admin') items.push(link('Admin', 'admin'));
  if (App.token) {
    items.push(el('span', { class: 'who' }, 'Hi, ' + (App.name || 'user')),
      el('button', { onclick: logout }, 'Logout'));
  } else {
    items.push(link('Login / Register', 'auth'));
  }
  nav.replaceChildren(...items);
}

async function logout() {
  try { await api('/api/auth/logout', { method: 'POST' }); } catch (e) { /* already expired */ }
  clearSession(); renderNav(); show('catalogue'); toast('Logged out');
}
