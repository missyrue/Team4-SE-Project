/* Administrator console: books, categories, inventory, orders, reports, audit log
 * (OBS-F-020..026, OBS-NF-006)  - owner: Aditya                                       */
App.views.admin = function (container) {
  const content = el('div', { id: 'admin-content' });
  const tabs = el('div', { class: 'tabs', id: 'admin-tabs' });
  const TABS = {
    books: ['Books', booksTab], categories: ['Categories', categoriesTab], inventory: ['Inventory', inventoryTab],
    orders: ['Orders', ordersTab], reports: ['Reports', reportsTab], audit: ['Audit log', auditTab],
  };

  function open(key) {
    [...tabs.children].forEach(b => b.classList.toggle('active', b.dataset.tab === key));
    content.replaceChildren(el('p', { class: 'muted' }, 'Loading…'));
    TABS[key][1](content).catch(e => { content.replaceChildren(el('p', { class: 'muted' }, e.message)); toast(e.message, true); });
  }

  tabs.replaceChildren(...Object.entries(TABS).map(([key, [label]]) => el('button', { 'data-tab': key, onclick: () => open(key) }, label)));
  container.replaceChildren(el('h2', {}, 'Administrator console'), tabs, content);
  open('books');

  // ------------------------------------------------------------------ books
  async function booksTab(box) {
    const [books, cats] = await Promise.all([api('/api/admin/books'), api('/api/categories')]);
    const editing = { id: null };
    const f = {
      title: el('input', { id: 'b-title', maxlength: '200' }), author: el('input', { id: 'b-author', maxlength: '100' }),
      isbn: el('input', { id: 'b-isbn' }), price: el('input', { id: 'b-price', type: 'number', min: '0.01', step: '0.01' }),
      category: el('select', { id: 'b-category' }, cats.map(c => el('option', { value: c.id }, c.name))),
      stock: el('input', { id: 'b-stock', type: 'number', min: '0', value: '10' }),
      reorder: el('input', { id: 'b-reorder', type: 'number', min: '0', value: '5' }),
      description: el('textarea', { id: 'b-description', maxlength: '2000' }),
    };
    const heading = el('h3', {}, 'Add a book');
    const submit = el('button', { class: 'btn', id: 'b-save', type: 'submit' }, 'Add book');

    function startEdit(b) {
      editing.id = b.id;
      f.title.value = b.title; f.author.value = b.author; f.isbn.value = b.isbn; f.isbn.disabled = true;   // ISBN is fixed after creation
      f.price.value = b.price; f.description.value = b.description || '';
      [...f.category.options].forEach(o => { if (o.text === b.category) f.category.value = o.value; });
      f.stock.disabled = f.reorder.disabled = true;                                                         // stock has its own tab
      heading.textContent = 'Edit book #' + b.id; submit.textContent = 'Save changes';
      heading.scrollIntoView({ behavior: 'smooth' });
    }

    async function save(e) {
      e.preventDefault();
      try {
        if (editing.id) {
          await api('/api/admin/books/' + editing.id, { method: 'PUT', body: { title: f.title.value, author: f.author.value, price: Number(f.price.value), categoryId: Number(f.category.value), description: f.description.value } });
          toast('Book updated');
        } else {
          await api('/api/admin/books', { method: 'POST', body: { title: f.title.value, author: f.author.value, isbn: f.isbn.value, price: Number(f.price.value), categoryId: Number(f.category.value), stock: Number(f.stock.value), reorderLevel: Number(f.reorder.value), description: f.description.value } });
          toast('Book added');
        }
        open('books');
      } catch (err) { toast(err.message, true); }
    }

    async function toggle(b) {
      try { await api('/api/admin/books/' + b.id, { method: 'PUT', body: { isActive: !b.isActive } }); toast(b.isActive ? 'Book deactivated' : 'Book activated'); open('books'); }
      catch (err) { toast(err.message, true); }
    }

    const rows = books.map(b => el('tr', {},
      el('td', {}, b.id), el('td', {}, b.title), el('td', {}, b.author), el('td', {}, money(b.price)), el('td', {}, b.stock),
      el('td', {}, el('span', { class: 'badge ' + (b.isActive ? 'ok' : 'bad') }, b.isActive ? 'Active' : 'Inactive')),
      el('td', {}, el('button', { class: 'btn secondary small', onclick: () => startEdit(b) }, 'Edit'), ' ',
        el('button', { class: 'btn small ' + (b.isActive ? 'danger' : 'ok'), onclick: () => toggle(b) }, b.isActive ? 'Deactivate' : 'Activate'))));

    box.replaceChildren(
      el('form', { class: 'card', id: 'book-form', onsubmit: save }, heading,
        el('div', { class: 'row' }, field('Title', f.title), field('Author', f.author), field('ISBN', f.isbn)),
        el('div', { class: 'row' }, field('Price (₹)', f.price), field('Category', f.category), field('Stock', f.stock), field('Reorder level', f.reorder)),
        field('Description', f.description), submit),
      el('h3', {}, `All books (${books.length}${books.length === 200 ? '+' : ''})`),
      table(['ID', 'Title', 'Author', 'Price', 'Stock', 'Status', 'Actions'], rows));
  }

  // ------------------------------------------------------------- categories
  async function categoriesTab(box) {
    const cats = await api('/api/categories');
    const name = el('input', { id: 'cat-name', maxlength: '60', placeholder: 'New category name' });
    async function add(e) {
      e.preventDefault();
      try { await api('/api/admin/categories', { method: 'POST', body: { name: name.value } }); toast('Category added'); open('categories'); }
      catch (err) { toast(err.message, true); }
    }
    const rows = cats.map(c => {
      const input = el('input', { value: c.name, maxlength: '60', 'aria-label': 'Name of category ' + c.id });
      return el('tr', {}, el('td', {}, c.id), el('td', {}, input),
        el('td', {}, el('button', { class: 'btn small', onclick: async () => {
          try { await api('/api/admin/categories/' + c.id, { method: 'PUT', body: { name: input.value } }); toast('Category renamed'); open('categories'); }
          catch (err) { toast(err.message, true); }
        } }, 'Save')));
    });
    box.replaceChildren(
      el('form', { class: 'card row', onsubmit: add }, field('New category', name), el('button', { class: 'btn shrink', type: 'submit' }, 'Add')),
      el('h3', {}, 'Categories'), table(['ID', 'Name', ''], rows));
  }

  // -------------------------------------------------------------- inventory
  async function inventoryTab(box) {
    const lowOnly = el('input', { type: 'checkbox', id: 'low-only' });
    const holder = el('div');
    async function load() {
      const data = lowOnly.checked ? (await api('/api/admin/inventory/low-stock')).books : await api('/api/admin/books');
      const rows = data.map(b => {
        const stock = el('input', { type: 'number', min: '0', value: String(b.stock), 'aria-label': 'Stock for ' + b.title });
        const reorder = el('input', { type: 'number', min: '0', value: String(b.reorderLevel), 'aria-label': 'Reorder level for ' + b.title });
        const tr = el('tr', { class: b.lowStock ? 'low' : '' }, el('td', {}, b.title),
          el('td', {}, stock), el('td', {}, reorder),
          el('td', {}, b.lowStock ? el('span', { class: 'badge warn' }, 'Low stock') : el('span', { class: 'badge ok' }, 'OK')),
          el('td', {}, el('button', { class: 'btn small', onclick: async () => {
            try {
              const r = await api('/api/admin/inventory/' + b.id, { method: 'PUT', body: { stock: Number(stock.value), reorderLevel: Number(reorder.value) } });
              toast(r.lowStock ? `Saved - LOW STOCK: only ${r.stock} left` : 'Inventory updated', r.lowStock);
              load();
            } catch (err) { toast(err.message, true); }
          } }, 'Save')));
        return tr;
      });
      holder.replaceChildren(rows.length ? table(['Book', 'Stock', 'Reorder level', 'Status', ''], rows) : el('p', { class: 'muted' }, 'No books to show.'));
    }
    lowOnly.addEventListener('change', load);
    box.replaceChildren(el('label', {}, lowOnly, ' Show only books at or below their reorder level'), holder);
    await load();
  }

  // ----------------------------------------------------------------- orders
  async function ordersTab(box) {
    const orders = await api('/api/admin/orders');
    const NEXT = { pending_payment: ['cancelled'], paid: ['processing', 'cancelled'], processing: ['shipped', 'cancelled'], shipped: ['delivered'] };
    const rows = orders.map(o => {
      const options = NEXT[o.status] || [];
      const select = el('select', { 'aria-label': 'New status for order ' + o.orderId }, options.map(s => el('option', { value: s }, s)));
      return el('tr', {}, el('td', {}, o.orderNumber || ('#' + o.orderId)), el('td', {}, 'User ' + o.customerId),
        el('td', {}, o.items.map(i => `${i.quantity}× ${i.title}`).join(', ')), el('td', {}, money(o.total)),
        el('td', {}, el('span', { class: 'badge' }, o.status.replace('_', ' '))),
        el('td', {}, options.length ? el('div', { class: 'row' }, select, el('button', { class: 'btn small shrink', onclick: async () => {
          try { await api(`/api/admin/orders/${o.orderId}/status`, { method: 'PUT', body: { status: select.value } }); toast('Status updated'); open('orders'); }
          catch (err) { toast(err.message, true); }
        } }, 'Update')) : el('span', { class: 'muted' }, 'final')));
    });
    box.replaceChildren(orders.length ? table(['Order', 'Customer', 'Items', 'Total', 'Status', 'Change status'], rows) : el('p', { class: 'muted' }, 'No orders yet.'));
  }

  // ---------------------------------------------------------------- reports
  async function reportsTab(box) {
    const today = new Date().toISOString().slice(0, 10);
    const start = el('input', { type: 'date', id: 'r-start', value: today });
    const end = el('input', { type: 'date', id: 'r-end', value: today });
    const out = el('div', { id: 'report-out' });
    const stat = (label, value) => el('div', { class: 'stat' }, el('span', { class: 'muted' }, label), el('b', {}, String(value)));

    async function sales() {
      try {
        const r = await api(`/api/admin/reports/sales?start=${start.value}&end=${end.value}`);
        out.replaceChildren(el('h3', {}, `Sales ${r.period.start} to ${r.period.end}`),
          el('div', { class: 'stats' }, stat('Orders', r.orders), stat('Revenue', money(r.revenue)), stat('Items sold', r.itemsSold)),
          r.topBooks.length ? table(['Top books', 'Quantity'], r.topBooks.map(b => el('tr', {}, el('td', {}, b.title), el('td', {}, b.quantity)))) : el('p', { class: 'muted' }, 'No sales in this period.'));
      } catch (e) { toast(e.message, true); }
    }
    async function stock() {
      try {
        const r = await api('/api/admin/reports/inventory');
        out.replaceChildren(el('h3', {}, 'Inventory snapshot'),
          el('div', { class: 'stats' }, stat('Books', r.totalBooks), stat('Units in stock', r.totalUnits), stat('Out of stock', r.outOfStock), stat('At/below reorder level', r.lowStockCount)),
          r.lowStock.length ? table(['Low-stock book', 'Stock', 'Reorder level'], r.lowStock.map(b => el('tr', {}, el('td', {}, b.title), el('td', {}, b.stock), el('td', {}, b.reorderLevel)))) : null);
      } catch (e) { toast(e.message, true); }
    }
    box.replaceChildren(
      el('div', { class: 'card row' }, field('From', start), field('To', end),
        el('button', { class: 'btn shrink', id: 'btn-sales', onclick: sales }, 'Sales report'),
        el('button', { class: 'btn secondary shrink', id: 'btn-stock', onclick: stock }, 'Inventory report')), out);
    sales();
  }

  // -------------------------------------------------------------- audit log
  async function auditTab(box) {
    const log = await api('/api/admin/audit-log');
    const rows = log.map(r => el('tr', {}, el('td', {}, new Date(r.time + 'Z').toLocaleString()), el('td', {}, 'User ' + r.userId), el('td', {}, r.action), el('td', {}, r.record), el('td', {}, r.detail)));
    box.replaceChildren(el('p', { class: 'muted' }, 'Every administrator change is recorded: who, what, which record, when.'),
      log.length ? table(['Time', 'Admin', 'Action', 'Record', 'Detail'], rows) : el('p', { class: 'muted' }, 'No changes recorded yet.'));
  }
};
