/* Cart screen - SPRINT 1 version (OBS-F-009, 010, 011): view cart, change quantity, remove item.
 * Checkout and payment arrive in Sprint 2 (they replace this file).   Owner: Aaruni */
App.views.cart = async function (container) {
  const body = el('div', { id: 'cart-body' });
  container.replaceChildren(el('h2', {}, 'Your cart'), body);

  async function load() {
    try { render(await api('/api/cart')); } catch (e) { toast(e.message, true); }
  }
  async function change(bookId, quantity) {
    try { render(await api('/api/cart/items/' + bookId, { method: 'PUT', body: { quantity } })); }
    catch (e) { toast(e.message, true); load(); }        // e.g. "Only 3 copies available" -> reload the real values
  }
  async function remove(bookId) {
    try { render(await api('/api/cart/items/' + bookId, { method: 'DELETE' })); toast('Item removed'); }
    catch (e) { toast(e.message, true); }
  }

  function render(cart) {
    if (!cart.items.length) {
      body.replaceChildren(el('p', { class: 'muted', id: 'cart-empty' }, 'Your cart is empty. Browse the catalogue to add books.'));
      return;
    }
    const rows = cart.items.map(i => {
      const qty = el('input', { type: 'number', min: '1', max: String(i.stock), value: String(i.quantity), 'aria-label': 'Quantity for ' + i.title });
      qty.addEventListener('change', () => change(i.bookId, Number(qty.value)));
      return el('tr', {}, el('td', {}, i.title), el('td', {}, money(i.unitPrice)), el('td', {}, qty),
        el('td', {}, money(i.lineTotal)),
        el('td', {}, el('button', { class: 'btn danger small', onclick: () => remove(i.bookId) }, 'Remove')));
    });
    body.replaceChildren(
      table(['Book', 'Price', 'Qty', 'Line total', ''], rows),
      el('div', { class: 'totals' }, el('div', { class: 'grand', id: 'cart-total' }, 'Subtotal: ', money(cart.subtotal))),
      el('p', { class: 'muted' }, 'Checkout and payment open in Sprint 2.'));
  }
  load();
};
