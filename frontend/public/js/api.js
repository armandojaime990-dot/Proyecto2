/* Cliente de la API REST (probado con Jest usando un fetch simulado). */
(function (root) {
  var TOKEN_KEY = "token";
  var USER_KEY = "user";

  function createApiClient(fetchImpl, storage, baseUrl) {
    baseUrl = baseUrl || "/api";

    function getToken() {
      return storage.getItem(TOKEN_KEY);
    }

    function request(method, path, body) {
      var headers = { "Content-Type": "application/json" };
      var token = getToken();
      if (token) headers.Authorization = "Bearer " + token;
      return fetchImpl(baseUrl + path, {
        method: method,
        headers: headers,
        body: body === undefined ? undefined : JSON.stringify(body),
      }).then(function (res) {
        if (res.status === 204) return null;
        return res.json().then(function (data) {
          if (!res.ok) {
            if (res.status === 401) logout();
            var err = new Error((data && data.error) || "Error " + res.status);
            err.status = res.status;
            err.fields = (data && data.fields) || {};
            throw err;
          }
          return data;
        });
      });
    }

    function login(email, password) {
      return request("POST", "/auth/login", { email: email, password: password }).then(function (data) {
        storage.setItem(TOKEN_KEY, data.token);
        storage.setItem(USER_KEY, JSON.stringify(data.user));
        return data.user;
      });
    }

    function logout() {
      storage.removeItem(TOKEN_KEY);
      storage.removeItem(USER_KEY);
    }

    function currentUser() {
      var raw = storage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    }

    return {
      login: login,
      logout: logout,
      isAuthenticated: function () { return !!getToken(); },
      currentUser: currentUser,
      me: function () { return request("GET", "/auth/me").then(function (d) { return d.user; }); },
      listUsers: function () { return request("GET", "/users").then(function (d) { return d.users; }); },
      createUser: function (u) { return request("POST", "/users", u).then(function (d) { return d.user; }); },
      updateUser: function (id, u) { return request("PUT", "/users/" + id, u).then(function (d) { return d.user; }); },
      deleteUser: function (id) { return request("DELETE", "/users/" + id); },
    };
  }

  var api = { createApiClient: createApiClient };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ApiClient = api;
})(this);
