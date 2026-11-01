/* Catalogue screen: browse, search, filter, sort, book detail  (OBS-F-004..008)  - owner: Aanya */
(function () {
  const PAGE_SIZE = 12;
  const state = { offset: 0 };

  App.views.catalogue = async function (container) {
    const q = el('input', { type: 'search', id: 'q', placeholder: 'Title, author or ISBN' });
    const category = el('select', { id: 'category' }, el('option', { value: '' }, 'All categories'));
    const minPrice = el('input', { type: 'number', id: 'minPrice', min: '0', placeholder: '0' });
    const maxPrice = el('input', { type: 'number', id: 'maxPrice', min: '0', placeholder: 'any' });
    const sort = el('select', { id: 'sort' },
      el('option', { value: 'title_asc' }, 'Title A-Z'), el('option', { value: 'title_desc' }, 'Title Z-A'),
      el('option', { value: 'price_asc' }, 'Price low-high'), el('option', { value: 'price_desc' }, 'Price high-low'));
    const results = el('div', { id: 'results' });
    const detail = el('div', { id: 'detail' });
    const pager = el('div', { class: 'row', id: 'pager' });

    async function search(resetPage) {
      if (resetPage) state.offset = 0;
      const params = new URLSearchParams({ sort: sort.value, limit: PAGE_SIZE, offset: state.offset });
      if (q.value.trim()) params.set('q', q.value.trim());
      if (category.value) params.set('category', category.value);
      if (minPrice.value !== '') params.set('minPrice', minPrice.value);
      if (maxPrice.value !== '') params.set('maxPrice', maxPrice.value);
      try {
        const data = await api('/api/books/search?' + params);
        if (!data) {                                         // 204: nothing matched
          results.replaceChildren(el('p', { class: 'muted', id: 'no-results' }, 'No books found. Try a different search.'));
          pager.replaceChildren();
          return;
        }
        results.replaceChildren(el('div', { class: 'grid' }, data.results.map(bookCard)));
        const last = Math.min(state.offset + PAGE_SIZE, data.count);
        pager.replaceChildren(
          el('span', { class: 'muted' }, `Showing ${state.offset + 1}-${last} of ${data.count}`),
          el('button', { class: 'btn secondary small shrink', disabled: state.offset === 0, onclick: () => { state.offset -= PAGE_SIZE; search(false); } }, 'Previous'),
          el('button', { class: 'btn secondary small shrink', disabled: last >= data.count, onclick: () => { state.offset += PAGE_SIZE; search(false); } }, 'Next'));
      } catch (e) { toast(e.message, true); }
    }

    function bookCard(book) {
      const inStock = book.stock > 0;
      return el('div', { class: 'card book' },
        el('h4', { onclick: () => openDetail(book.id) }, book.title),
        el('div', { class: 'muted' }, book.author),
        el('div', {}, el('span', { class: 'badge' }, book.category || 'Uncategorised')),
        el('p', {}, el('span', { class: 'price' }, money(book.price)), ' ',
          el('span', { class: 'badge ' + (inStock ? 'ok' : 'bad') }, book.availability)),
        el('div', { class: 'row' },
          el('button', { class: 'btn secondary small', onclick: () => openDetail(book.id) }, 'Details'),
          el('button', { class: 'btn small', disabled: !inStock, onclick: () => addToCart(book.id, 1) }, 'Add to cart')));
    }

    async function openDetail(id) {
      try {
        const b = await api('/api/books/' + id);
        const qty = el('input', { type: 'number', min: '1', max: String(Math.max(b.stock, 1)), value: '1' });
        detail.replaceChildren(el('div', { class: 'card', id: 'book-detail' },
          el('h3', {}, b.title), el('p', { class: 'muted' }, 'by ' + b.author),
          el('p', {}, b.description || 'No description available.'),
          el('p', {}, el('b', {}, 'ISBN: '), b.isbn, '  ·  ', el('b', {}, 'Category: '), b.category || '-'),
          el('p', {}, el('span', { class: 'price' }, money(b.price)), '  ',
            el('span', { class: 'badge ' + (b.stock > 0 ? 'ok' : 'bad') }, b.availability + (b.stock > 0 ? ` (${b.stock} left)` : ''))),
          el('div', { class: 'row' },
            field('Quantity', qty),
            el('button', { class: 'btn shrink', disabled: b.stock <= 0, onclick: () => addToCart(b.id, Number(qty.value) || 1) }, 'Add to cart'),
            el('button', { class: 'btn secondary shrink', onclick: () => detail.replaceChildren() }, 'Close'))));
        detail.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } catch (e) { toast(e.message, true); }
    }

    container.replaceChildren(
      el('h2', {}, 'Browse books'),
      el('form', { class: 'card', id: 'search-form', onsubmit: (e) => { e.preventDefault(); search(true); } },
        el('div', { class: 'row' },
          field('Search', q), field('Category', category), field('Min price', minPrice), field('Max price', maxPrice), field('Sort by', sort),
          el('button', { class: 'btn shrink', type: 'submit' }, 'Search'))),
      detail, el('div', { style: 'height:12px' }), results, el('div', { style: 'height:12px' }), pager);

    try {                                                    // fill the category drop-down
      const cats = await api('/api/categories');
      cats.forEach(c => category.append(el('option', { value: c.name }, c.name)));
    } catch (e) { /* filter just stays on "All" */ }
    search(true);
  };
})();
