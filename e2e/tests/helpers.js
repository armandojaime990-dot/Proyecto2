const ADMIN = {
  email: process.env.E2E_ADMIN_EMAIL || "admin@demo.com",
  password: process.env.E2E_ADMIN_PASSWORD || "Admin123!",
};

function uniqueEmail(prefix = "e2e") {
  return `${prefix}.${Date.now()}.${Math.floor(Math.random() * 1000)}@test.com`;
}

async function apiToken(request) {
  const res = await request.post("/api/auth/login", { data: ADMIN });
  return (await res.json()).token;
}

async function uiLogin(page) {
  await page.goto("/");
  await page.getByTestId("login-email").fill(ADMIN.email);
  await page.getByTestId("login-password").fill(ADMIN.password);
  await page.getByTestId("login-submit").click();
  await page.waitForURL("**/users.html");
}

module.exports = { ADMIN, uniqueEmail, apiToken, uiLogin };
