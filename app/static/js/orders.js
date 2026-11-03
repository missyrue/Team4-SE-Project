/* My orders screen: history, status, cancel  (OBS-F-018, OBS-F-019)  - owner: Aaruni */
App.views.orders = async function (container) {
  const list = el('div', { id: 'order-list' });
  container.replaceChildren(el('h2', {}, 'My orders'), list);

  const CANCELLABLE = ['pending_payment', 'paid', 'processing'];
  const BADGE = { pending_payment: 'warn', payment_failed: 'bad', cancelled: 'bad', paid: 'ok', processing: 'ok', shipped: 'ok', delivered: 'ok' };

  async function cancel(id) {
    if (!confirm('Cancel this order?')) return;
    try { await api(`/api/orders/${id}/cancel`, { method: 'POST' }); toast('Order cancelled'); load(); }
    catch (e) { toast(e.message, true); }
  }

  function card(o) {
    return el('div', { class: 'card', style: 'margin-bottom:12px' },
      el('div', { class: 'row' },
        el('div', {}, el('b', {}, o.orderNumber || ('Order #' + o.orderId)), ' ',
          el('span', { class: 'badge ' + (BADGE[o.status] || '') }, o.status.replace('_', ' '))),
        el('div', { class: 'muted shrink' }, new Date(o.createdAt + 'Z').toLocaleString())),
      el('ul', {}, o.items.map(i => el('li', {}, `${i.quantity} × ${i.title} (${money(i.unitPrice)})`))),
      el('p', {}, 'Total: ', el('b', {}, money(o.total)), '  ·  Deliver to: ', o.deliveryAddress),
      CANCELLABLE.includes(o.status) && el('button', { class: 'btn danger small', onclick: () => cancel(o.orderId) }, 'Cancel order'));
  }

  async function load() {
    try {
      const orders = await api('/api/orders');
      list.replaceChildren(...(orders.length ? orders.map(card) : [el('p', { class: 'muted', id: 'no-orders' }, 'You have not placed any orders yet.')]));
    } catch (e) { toast(e.message, true); }
  }
  load();
};
