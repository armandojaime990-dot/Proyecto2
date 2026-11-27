# Proyecto Parcial 2: CI/CD, Pruebas Automatizadas y Observabilidad

Sistema de **Login + CRUD de usuarios** con:

- **Backend:** Python/Flask + PostgreSQL + JWT, probado con **pytest**
- **Frontend:** HTML/JS servido con nginx, probado con **Jest**
- **E2E:** **Playwright** (interfaz y API)
- **Total: 550 pruebas** (300 pytest + 150 Jest + 100 Playwright)
- **CI/CD:** GitHub Actions → AWS EC2 (despliega **solo** si pasan las pruebas)
- **Observabilidad:** OpenTelemetry (OTLP) → **OpenObserve** (logs, métricas y trazas), eventos del pipeline
  y recursos del servidor (CPU, RAM, red y temperatura)

```
├── backend/            API Flask (auth, users, telemetry) + tests pytest
├── frontend/           index.html (login), users.html (CRUD) + tests Jest
├── e2e/                Pruebas Playwright (ui-*.spec.js, api-*.spec.js)
├── host-agent/         Agente de métricas de la EC2 → OpenObserve
├── scripts/            send_o2_event.sh, setup-ec2.sh, generate_traffic.sh
├── .github/workflows/  ci-cd.yml
└── docker-compose.yml
```

**Instrucciones completas:** [GUIA_PASO_A_PASO.md](GUIA_PASO_A_PASO.md)

| Servicio | URL | Usuario | Contraseña |
|---|---|---|---|
| Aplicación | `http://TU_IP` | admin@demo.com | Admin123! |
| OpenObserve | `http://TU_IP:5080` | admin@demo.com | Observe2026! |
