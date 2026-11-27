(function () {
  var api = ApiClient.createApiClient(window.fetch.bind(window), window.localStorage);
  if (api.isAuthenticated()) window.location.href = "/users.html";

  var form = document.getElementById("login-form");
  var alertBox = document.querySelector("[data-testid=login-error]");

  function showFieldErrors(errors) {
    ["email", "password"].forEach(function (f) {
      document.querySelector("[data-testid=error-" + f + "]").textContent = errors[f] || "";
    });
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    alertBox.hidden = true;
    var data = { email: form.elements.email.value, password: form.elements.password.value };
    var errors = Validation.validateLoginForm(data);
    showFieldErrors(errors);
    if (Validation.hasErrors(errors)) return;

    var btn = form.querySelector("button");
    btn.disabled = true;
    api.login(data.email.trim(), data.password)
      .then(function () { window.location.href = "/users.html"; })
      .catch(function (err) {
        alertBox.textContent = err.message;
        alertBox.hidden = false;
      })
      .finally(function () { btn.disabled = false; });
  });
})();
