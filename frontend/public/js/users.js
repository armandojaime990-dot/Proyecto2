(function () {
  var api = ApiClient.createApiClient(window.fetch.bind(window), window.localStorage);
  if (!api.isAuthenticated()) { window.location.href = "/"; return; }

  var $ = function (id) { return document.querySelector("[data-testid=" + id + "]"); };
  var tbody = $("users-tbody");
  var modal = $("user-modal");
  var form = document.getElementById("user-form");
  var F = form.elements;
  var confirmModal = $("confirm-modal");
  var pendingDelete = null;
  var me = api.currentUser();

  $("current-user").textContent = me ? me.name + " (" + me.role + ")" : "";

  function goLogin() { api.logout(); window.location.href = "/"; }

  function handleError(err) {
    if (err.status === 401) return goLogin();
    flash(err.message, true);
  }

  function flash(msg, isError) {
    var el = $("flash");
    el.textContent = msg;
    el.className = "alert " + (isError ? "" : "success");
    el.hidden = false;
    clearTimeout(flash._t);
    flash._t = setTimeout(function () { el.hidden = true; }, 4000);
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function render(users) {
    tbody.innerHTML = users.map(function (u) {
      return '<tr data-testid="user-row" data-email="' + escapeHtml(u.email) + '">' +
        "<td>" + u.id + "</td><td>" + escapeHtml(u.name) + "</td><td>" + escapeHtml(u.email) + "</td>" +
        "<td>" + escapeHtml(u.role) + "</td>" +
        '<td><button class="btn" data-action="edit" data-id="' + u.id + '" data-testid="edit-' + u.id + '">Editar</button> ' +
        '<button class="btn danger" data-action="delete" data-id="' + u.id + '" data-testid="delete-' + u.id + '">Eliminar</button></td>' +
        "</tr>";
    }).join("");
    tbody._users = users;
  }

  function load() { return api.listUsers().then(render).catch(handleError); }

  function setErrors(errors) {
    ["name", "email", "password", "role"].forEach(function (f) {
      form.querySelector("[data-testid=error-" + f + "]").textContent = errors[f] || "";
    });
  }

  function openModal(user) {
    form.reset();
    setErrors({});
    $("form-error").hidden = true;
    F.userId.value = user ? user.id : "";
    $("modal-title").textContent = user ? "Editar usuario" : "Nuevo usuario";
    $("pwd-hint").textContent = user ? "(dejar vacía para no cambiarla)" : "";
    if (user) {
      F.name.value = user.name;
      F.email.value = user.email;
      F.role.value = user.role;
    }
    modal.hidden = false;
    F.name.focus();
  }

  $("new-user").addEventListener("click", function () { openModal(null); });
  $("cancel").addEventListener("click", function () { modal.hidden = true; });
  $("logout").addEventListener("click", goLogin);

  tbody.addEventListener("click", function (ev) {
    var btn = ev.target.closest("button[data-action]");
    if (!btn) return;
    var id = Number(btn.dataset.id);
    var user = (tbody._users || []).filter(function (u) { return u.id === id; })[0];
    if (btn.dataset.action === "edit") openModal(user);
    else {
      pendingDelete = user;
      $("confirm-text").textContent = "¿Eliminar al usuario " + user.email + "?";
      confirmModal.hidden = false;
    }
  });

  $("confirm-no").addEventListener("click", function () { confirmModal.hidden = true; });
  $("confirm-yes").addEventListener("click", function () {
    var user = pendingDelete;
    confirmModal.hidden = true;
    api.deleteUser(user.id)
      .then(function () { flash("Usuario eliminado"); return load(); })
      .catch(handleError);
  });

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var isEdit = !!F.userId.value;
    var data = {
      name: F.name.value.trim(),
      email: F.email.value.trim(),
      password: F.password.value,
      role: F.role.value,
    };
    var errors = Validation.validateUserForm(data, isEdit);
    setErrors(errors);
    if (Validation.hasErrors(errors)) return;
    if (isEdit && !data.password) delete data.password;

    var action = isEdit ? api.updateUser(F.userId.value, data) : api.createUser(data);
    action
      .then(function () {
        modal.hidden = true;
        flash(isEdit ? "Usuario actualizado" : "Usuario creado");
        return load();
      })
      .catch(function (err) {
        if (err.status === 401) return goLogin();
        setErrors(err.fields || {});
        $("form-error").textContent = err.message;
        $("form-error").hidden = false;
      });
  });

  load();
})();
