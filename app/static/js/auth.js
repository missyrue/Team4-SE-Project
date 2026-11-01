/* Login / Register screen  (OBS-F-001, OBS-F-002)  - owner: Aanya */
App.views.auth = function (container) {
  const loginEmail = el('input', { type: 'email', id: 'login-email', autocomplete: 'username', required: true });
  const loginPass = el('input', { type: 'password', id: 'login-password', autocomplete: 'current-password', required: true });
  const loginMsg = el('p', { class: 'muted', id: 'login-msg' });

  const regName = el('input', { type: 'text', id: 'reg-name', maxlength: '100', required: true });
  const regEmail = el('input', { type: 'email', id: 'reg-email', autocomplete: 'email', required: true });
  const regPass = el('input', { type: 'password', id: 'reg-password', autocomplete: 'new-password', minlength: '8', required: true });
  const regMsg = el('p', { class: 'muted', id: 'reg-msg' });

  async function doLogin(event) {
    event.preventDefault();
    loginMsg.textContent = '';
    try {
      const data = await api('/api/auth/login', { method: 'POST', body: { email: loginEmail.value, password: loginPass.value } });
      saveSession(data.token, data.role, data.fullName);
      renderNav();
      toast('Welcome, ' + data.fullName);
      show(data.role === 'admin' ? 'admin' : 'catalogue');
    } catch (e) { loginMsg.textContent = e.message; toast(e.message, true); }
  }

  async function doRegister(event) {
    event.preventDefault();
    regMsg.textContent = '';
    try {
      await api('/api/auth/register', { method: 'POST', body: { email: regEmail.value, password: regPass.value, fullName: regName.value } });
      loginEmail.value = regEmail.value; loginPass.value = '';
      regMsg.textContent = 'Account created! You can now log in on the left.';
      toast('Account created. Please log in.');
    } catch (e) { regMsg.textContent = e.message; toast(e.message, true); }
  }

  container.replaceChildren(
    el('h2', {}, 'Welcome'),
    el('div', { class: 'two-col' },
      el('form', { class: 'card', id: 'login-form', onsubmit: doLogin },
        el('h3', {}, 'Login'),
        field('Email', loginEmail), field('Password', loginPass),
        el('button', { class: 'btn', type: 'submit' }, 'Login'), loginMsg),
      el('form', { class: 'card', id: 'register-form', onsubmit: doRegister },
        el('h3', {}, 'Create account'),
        field('Full name', regName), field('Email', regEmail),
        field('Password (min 8 characters, letters + a digit)', regPass),
        el('button', { class: 'btn secondary', type: 'submit' }, 'Register'), regMsg)));
};
