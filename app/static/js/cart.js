/* Cart + checkout + payment screen  (OBS-F-009..017)  - owner: Aaruni */
App.views.cart = async function (container) {
  const body = el('div', { id: 'cart-body' });
  container.replaceChildren(el('h2', {}, 'Your cart'), body);

  async function load() {
    try { render(await api('/api/cart')); } catch (e) { toast(e.message, true); }
  }

  async function change(bookId, quantity) {
    try { render(await api('/api/cart/items/' + bookId, { method: 'PUT', body: { quantity } })); }
    catch (e) { toast(e.message, true); load(); }           // e.g. "Only 3 copies available" -> reload real values
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

    const address = el('textarea', { id: 'address', placeholder: 'House no, street, city, PIN code' });
    const phone = el('input', { type: 'tel', id: 'phone', placeholder: '10-digit mobile number' });
    const checkoutMsg = el('p', { class: 'muted', id: 'checkout-msg' });

    async function placeOrder() {
      checkoutMsg.textContent = '';
      try {
        const order = await api('/api/orders/checkout', { method: 'POST', body: { cartId: cart.cartId, deliveryAddress: address.value, contactDetails: phone.value } });
        showPayment(order);
      } catch (e) { checkoutMsg.textContent = e.message; toast(e.message, true); }
    }

    body.replaceChildren(
      table(['Book', 'Price', 'Qty', 'Line total', ''], rows),
      el('div', { class: 'totals' },
        el('div', {}, 'Subtotal: ', money(cart.subtotal)),
        cart.discount > 0 && el('div', {}, 'Discount (10%): -', money(cart.discount)),
        el('div', {}, 'Delivery: ', cart.deliveryCharge === 0 ? 'FREE' : money(cart.deliveryCharge)),
        el('div', { class: 'grand', id: 'cart-total' }, 'Total: ', money(cart.total))),
      el('div', { class: 'card', id: 'checkout-form' },
        el('h3', {}, 'Delivery details'),
        field('Delivery address', address), field('Contact number', phone),
        el('button', { class: 'btn', id: 'place-order', onclick: placeOrder }, 'Place order & pay'), checkoutMsg));
  }

  // Step 2: the (mock) payment gateway. A real gateway would be a redirect; here we simulate it.
  function showPayment(order) {
    const result = el('p', { id: 'payment-result', class: 'muted' });

    async function pay(outcome) {
      try {
        const signed = await api('/api/mock-gateway/pay', { method: 'POST', body: { paymentRequestId: order.paymentRequestId, outcome }, auth: false });
        const done = await api(`/api/orders/${order.orderId}/payment-result`, { method: 'POST', body: signed, auth: false });   // gateway callback: proven by signature, not by login
        if (done.status === 'paid') {
          result.textContent = 'Payment successful! Order number: ' + done.orderNumber;
          toast('Order confirmed: ' + done.orderNumber);
          setTimeout(() => show('orders'), 1500);
        } else {
          result.textContent = 'Payment failed. Nothing was charged and your stock was not touched. Your cart is kept so you can try again.';
          toast('Payment failed', true);
        }
      } catch (e) {
        result.textContent = 'Payment rejected: ' + e.message;     // e.g. "Invalid payment signature"
        toast(e.message, true);
      }
    }

    body.replaceChildren(el('div', { class: 'card', id: 'payment-panel' },
      el('h3', {}, 'Payment (demo gateway)'),
      el('p', {}, 'Amount to pay: ', el('b', {}, money(order.total))),
      el('p', { class: 'muted' }, 'This is a simulated payment service. Pick what the gateway should answer:'),
      el('div', { class: 'row' },
        el('button', { class: 'btn ok', id: 'pay-success', onclick: () => pay('success') }, 'Pay successfully'),
        el('button', { class: 'btn danger', id: 'pay-failed', onclick: () => pay('failed') }, 'Simulate failed payment'),
        el('button', { class: 'btn secondary', id: 'pay-tampered', onclick: () => pay('tampered') }, 'Simulate tampered result')),
      result,
      el('button', { class: 'btn secondary small', onclick: load }, 'Back to cart')));
  }

  load();
};
