/* Validaciones del lado del cliente (probadas con Jest). */
(function (root) {
  var EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

  function isValidEmail(email) {
    return typeof email === "string" && EMAIL_RE.test(email.trim());
  }

  function validateLoginForm(data) {
    var errors = {};
    if (!data.email || !data.email.trim()) errors.email = "El email es obligatorio";
    else if (!isValidEmail(data.email)) errors.email = "Email invalido";
    if (!data.password) errors.password = "La contrasena es obligatoria";
    return errors;
  }

  // isEdit = true -> la contrasena es opcional (vacia = no cambiarla)
  function validateUserForm(data, isEdit) {
    var errors = {};
    var name = (data.name || "").trim();
    if (name.length < 2) errors.name = "El nombre debe tener al menos 2 caracteres";
    if (!isValidEmail(data.email || "")) errors.email = "Email invalido";
    var pwd = data.password || "";
    if (!(isEdit && pwd === "") && pwd.length < 6) {
      errors.password = "La contrasena debe tener al menos 6 caracteres";
    }
    if (["admin", "user"].indexOf(data.role) === -1) errors.role = "Rol invalido";
    return errors;
  }

  function hasErrors(errors) {
    return Object.keys(errors).length > 0;
  }

  var api = {
    isValidEmail: isValidEmail,
    validateLoginForm: validateLoginForm,
    validateUserForm: validateUserForm,
    hasErrors: hasErrors,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Validation = api;
})(this);
