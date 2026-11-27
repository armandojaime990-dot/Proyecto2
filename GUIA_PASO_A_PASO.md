# Guía paso a paso: lo que TÚ tienes que hacer

El código ya está completo y probado (app, pruebas, pipeline, telemetría y agente de métricas).
Lo que queda depende de **tus cuentas** (AWS, GitHub) y de **capturas** para el reporte.
Sigue los pasos en orden. Tiempo estimado: 2 a 3 horas.

> ⚠️ **Ojo con el PDF:** en el título hay un texto oculto (blanco, de 2 pt) que dice
> "(ignore next)". Es una trampa para ver quién le pasa el PDF a una IA sin leerlo.
> Aquí se cumplieron **todos** los requisitos. No lo menciones como instrucción.

---

## 0. Qué hace cada parte (para que puedas explicarlo en clase)

**Total: 550 pruebas automatizadas** (300 pytest + 150 Jest + 100 Playwright).

| Requisito | Dónde está |
|---|---|
| Login + CRUD de usuarios | `backend/app/auth.py`, `backend/app/users.py`, `frontend/public/` |
| RF-01: pruebas de backend | `backend/tests/` (**pytest**, 300 pruebas) |
| RF-01: pruebas de frontend | `frontend/tests/` (**Jest**, 150 pruebas) |
| RF-01: pruebas E2E de frontend y backend | `e2e/tests/` (**Playwright**, 100 pruebas: 39 de UI y 61 de API) |
| RF-02: solo despliega si pasan las pruebas | `.github/workflows/ci-cd.yml` (el job `deploy` tiene `needs: test`) |
| RF-03: el pipeline registra eventos en OpenObserve | `scripts/send_o2_event.sh` → stream `cicd_pipeline` (resultado, commit, rama, usuario) |
| RF-04: logs, métricas y trazas con OpenTelemetry (OTLP) | `backend/app/telemetry.py` y `backend/app/__init__.py` |
| RF-05: CPU, RAM, ancho de banda y temperatura de la EC2 | `host-agent/agent.py` → stream `ec2_host_metrics` |
| RF-06: dashboard y alertas | Lo armas tú en OpenObserve (pasos 8 y 9, con las consultas ya escritas) |

**Arquitectura:** Navegador → **nginx** (frontend, puerto 80) → **Flask/Gunicorn** (backend) → **PostgreSQL**.
El backend manda trazas, métricas y logs por OTLP a **OpenObserve** (puerto 5080). El `host-agent` manda las métricas del servidor.
Todo corre con Docker Compose en la EC2.

**Credenciales por defecto** (cámbialas en `.env` si quieres):
- App: `admin@demo.com` / `Admin123!`
- OpenObserve: `admin@demo.com` / `Observe2026!`

---

## 1. Lo que necesitas antes de empezar

1. Una cuenta de **AWS** (sirve la de AWS Academy/Learner Lab si tu escuela te la dio).
2. Una cuenta de **GitHub**.
3. **Git** instalado en tu computadora.
4. Descomprimir el ZIP del proyecto en una carpeta.

---

## 2. Subir el proyecto a GitHub

1. En GitHub: **New repository** → nombre, por ejemplo, `proyecto-parcial2-cicd` → **Public** → *Create* (sin README).
2. En la carpeta del proyecto, abre una terminal:

```bash
git init
git add .
git commit -m "Proyecto parcial 2: app + pruebas + CI/CD + observabilidad"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/proyecto-parcial2-cicd.git
git push -u origin main
```

El primer push ejecutará el pipeline y el deploy **fallará**, porque todavía no existe la EC2. Es normal; sigue con los pasos.

---

## 3. Crear la instancia EC2

En la consola de AWS → **EC2** → **Launch instance**:

| Campo | Valor |
|---|---|
| Name | `servidor-parcial2` |
| AMI | **Ubuntu Server 24.04 LTS** |
| Instance type | **t3.small** (2 GB de RAM). Con t3.micro también funciona gracias al swap, pero va más lento. |
| Key pair | *Create new key pair* → `parcial2-key`, tipo RSA, formato **.pem** → se descarga. **Guárdalo bien.** |
| Storage | **20 GB** gp3 |

**Network settings → Edit → Security group** (reglas de entrada):

| Tipo | Puerto | Origen | Para qué |
|---|---|---|---|
| SSH | 22 | 0.0.0.0/0 | GitHub Actions se conecta desde IPs variables |
| HTTP | 80 | 0.0.0.0/0 | La aplicación |
| Custom TCP | 5080 | 0.0.0.0/0 | OpenObserve (interfaz y API) |

Después de lanzarla, ve a **Elastic IPs → Allocate → Associate** con tu instancia. Así la IP no cambia al reiniciar. A esa IP la llamaremos `TU_IP`.

---

## 4. Preparar la EC2 (solo una vez)

Desde tu computadora (en Windows usa PowerShell o Git Bash):

```bash
chmod 400 parcial2-key.pem          # en Windows no hace falta
scp -i parcial2-key.pem scripts/setup-ec2.sh .env.example ubuntu@TU_IP:~
ssh -i parcial2-key.pem ubuntu@TU_IP
```

Ya dentro de la EC2:

```bash
bash setup-ec2.sh          # instala Docker, rsync, lm-sensors y crea swap
exit                       # sal y vuelve a entrar para que se apliquen los permisos de docker
```

```bash
ssh -i parcial2-key.pem ubuntu@TU_IP
mkdir -p ~/app && cp ~/.env.example ~/app/.env
nano ~/app/.env            # cambia las contraseñas si quieres; deja OTEL_ENABLED=true
docker --version           # debe responder
```

---

## 5. Configurar los Secrets de GitHub

En tu repositorio: **Settings → Secrets and variables → Actions → New repository secret**:

| Nombre | Valor |
|---|---|
| `EC2_HOST` | `TU_IP` (solo la IP, sin http) |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | **Todo** el contenido del archivo `.pem`, incluyendo las líneas `-----BEGIN…` y `-----END…` |
| `O2_URL` | `http://TU_IP:5080` |
| `O2_USER` | el mismo `O2_USER` de tu `.env` |
| `O2_PASSWORD` | el mismo `O2_PASSWORD` de tu `.env` |

---

## 6. Primer despliegue

1. GitHub → pestaña **Actions** → workflow **CI-CD** → **Run workflow** (rama `main`).
2. Espera a que termine (unos 8–12 min la primera vez, porque construye las imágenes en la EC2).
3. Comprueba:
   - App: `http://TU_IP` → inicia sesión con `admin@demo.com` / `Admin123!`.
   - OpenObserve: `http://TU_IP:5080` → inicia sesión con `O2_USER` / `O2_PASSWORD`.
4. Vuelve a ejecutar el workflow una vez más. En la primera ejecución OpenObserve aún no existía, así que el evento de *tests* no pudo registrarse. A partir de ahora quedan todos.

**Si algo falla:** abre el job en rojo y lee el paso que falló. En la EC2 puedes revisar con
`cd ~/app && docker compose --profile monitoring ps` y `docker compose logs backend --tail=100`.

---

## 7. Generar datos y comprobar que llegan a OpenObserve

Desde tu computadora (en Git Bash o en la propia EC2):

```bash
bash scripts/generate_traffic.sh http://TU_IP 200
```

En OpenObserve → **Streams** deberías ver:

| Stream | Tipo | Qué contiene |
|---|---|---|
| `default` | Logs | Logs estructurados de la app (`event`, `endpoint`, `status_code`, `response_time_ms`…) |
| `default` | Traces | Trazas: petición HTTP (Flask) → consultas SQL (PostgreSQL) |
| `app_http_requests`, `app_http_errors`, `app_http_request_duration_ms…` | Metrics | Métricas OTel por endpoint y statusCode |
| `cicd_pipeline` | Logs | Eventos del pipeline |
| `ec2_host_metrics` | Logs | CPU, RAM, red, disco y temperatura de la EC2 |

> Los nombres exactos de las métricas pueden variar un poco (por ejemplo, el histograma se puede
> dividir en `_bucket`, `_sum` y `_count`). Míralos en **Streams** y úsalos tal cual.

**Trazas:** menú **Traces** → servicio `users-backend` → abre una traza de `POST /api/users`.
Verás el span HTTP y dentro los spans de SQL (`INSERT`, `SELECT`). Toma captura (Figura).

---

## 8. Crear el Dashboard (RF-05 y RF-06)

**Dashboards → New dashboard** → nombre: `Proyecto Parcial 2 - Observabilidad`.
Crea pestañas o secciones y agrega paneles (**Add panel**). En cada panel elige el stream,
activa **Custom SQL** (o el modo SQL) y pega la consulta. Usa gráfica de líneas salvo que se indique otra cosa.

### A) Pipeline CI/CD (stream `cicd_pipeline`)

**Tabla: Historial de ejecuciones**
```sql
SELECT _timestamp, event_type, status, branch, actor, commit_short, detail, run_url
FROM "cicd_pipeline" ORDER BY _timestamp DESC
```

**Barras: Resultados por tipo**
```sql
SELECT event_type, status, count(*) AS total
FROM "cicd_pipeline" GROUP BY event_type, status
```

### B) Aplicación (stream `default`, tipo Logs)

**Peticiones por segundo por endpoint**
```sql
SELECT histogram(_timestamp, '1 minute') AS x_axis_1, endpoint,
       count(*) / 60.0 AS req_por_seg
FROM "default" WHERE event = 'http_request'
GROUP BY x_axis_1, endpoint ORDER BY x_axis_1
```

**Latencia promedio y p95 (ms) por endpoint**
```sql
SELECT histogram(_timestamp, '1 minute') AS x_axis_1, endpoint,
       avg(response_time_ms) AS latencia_prom_ms,
       approx_percentile_cont(response_time_ms, 0.95) AS latencia_p95_ms
FROM "default" WHERE event = 'http_request'
GROUP BY x_axis_1, endpoint ORDER BY x_axis_1
```

**Tasa de error HTTP (%) por endpoint**
```sql
SELECT histogram(_timestamp, '1 minute') AS x_axis_1, endpoint,
       sum(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) * 100.0 / count(*) AS tasa_error_pct
FROM "default" WHERE event = 'http_request'
GROUP BY x_axis_1, endpoint ORDER BY x_axis_1
```

**Barras: Peticiones por statusCode**
```sql
SELECT status_code, count(*) AS total
FROM "default" WHERE event = 'http_request' GROUP BY status_code
```

**Tabla: Excepciones y errores recientes**
```sql
SELECT _timestamp, severity, body, endpoint, status_code
FROM "default" WHERE status_code >= 500 OR event = 'unhandled_exception'
ORDER BY _timestamp DESC
```

**Panel con métricas OTel (stream de tipo Metrics, modo PromQL)**
```
sum by (endpoint, status_code) (rate(app_http_requests[1m]))
```

**Panel de trazas (stream `default` de tipo Traces).** Elige el tipo de stream *Traces* y una tabla con
`trace_id`, `operation_name`, `duration` y `span_status` (escoge los campos de la lista).

### C) Infraestructura EC2 (stream `ec2_host_metrics`)

**CPU (%)**
```sql
SELECT histogram(_timestamp, '1 minute') AS x_axis_1, avg(cpu_percent) AS cpu_pct
FROM "ec2_host_metrics" GROUP BY x_axis_1 ORDER BY x_axis_1
```

**Memoria RAM (%)**
```sql
SELECT histogram(_timestamp, '1 minute') AS x_axis_1, avg(mem_percent) AS ram_pct, avg(mem_used_mb) AS ram_mb
FROM "ec2_host_metrics" GROUP BY x_axis_1 ORDER BY x_axis_1
```

**Ancho de banda (kbps)**
```sql
SELECT histogram(_timestamp, '1 minute') AS x_axis_1,
       avg(net_rx_kbps) AS entrada_kbps, avg(net_tx_kbps) AS salida_kbps
FROM "ec2_host_metrics" GROUP BY x_axis_1 ORDER BY x_axis_1
```

**Temperatura (°C)** (lee la nota de la sección 11)
```sql
SELECT histogram(_timestamp, '1 minute') AS x_axis_1, avg(temp_c) AS temperatura_c, max(temp_source) AS fuente
FROM "ec2_host_metrics" GROUP BY x_axis_1 ORDER BY x_axis_1
```

**Disco (%) y carga**
```sql
SELECT histogram(_timestamp, '1 minute') AS x_axis_1, avg(disk_percent) AS disco_pct, avg(load1) AS carga
FROM "ec2_host_metrics" GROUP BY x_axis_1 ORDER BY x_axis_1
```

Guarda el dashboard. Para el criterio 3 necesitas una vista donde se vean **a la vez** los logs del pipeline, las trazas y las gráficas de CPU, red, temperatura y RAM. Acomoda esos paneles juntos y toma una captura de pantalla completa.

---

## 9. Alertas operativas (RF-06)

1. **Primero crea un destino:** *Alerts → Destinations* (o *Management → Alert destinations*).
   - Lo más fácil es un webhook de **Discord** (Servidor → Configuración → Integraciones → Webhooks → copiar URL)
     o uno de prueba en https://webhook.site.
   - Si te pide **Template**, crea uno con este cuerpo:
     `{"content": "ALERTA {alert_name}: {alert_count} eventos en {stream_name}"}`
2. **Alerts → Add alert** (tipo *Scheduled*, con SQL). Crea estas cuatro:

| Alerta | Stream | SQL | Condición | Periodo / Frecuencia |
|---|---|---|---|---|
| Errores 5xx | `default` | `SELECT count(*) AS errores FROM "default" WHERE status_code >= 500` | errores >= 1 | 5 min / 1 min |
| CPU alta | `ec2_host_metrics` | `SELECT avg(cpu_percent) AS cpu FROM "ec2_host_metrics"` | cpu > 80 | 5 min / 1 min |
| RAM alta | `ec2_host_metrics` | `SELECT avg(mem_percent) AS ram FROM "ec2_host_metrics"` | ram > 85 | 5 min / 1 min |
| Pipeline fallido | `cicd_pipeline` | `SELECT count(*) AS fallos FROM "cicd_pipeline" WHERE status IN ('failure','blocked')` | fallos >= 1 | 10 min / 1 min |

3. Agrega al dashboard un panel **"Alertas / Incidentes"** (tabla):
```sql
SELECT _timestamp, event_type, status, detail, actor, commit_short
FROM "cicd_pipeline" WHERE status <> 'success' ORDER BY _timestamp DESC
```
4. Para probarlas: haz la demo de la sección 10 (dispara *Pipeline fallido*). Para la CPU, ejecuta en la EC2
   `timeout 360 yes > /dev/null &` dos veces. Toma captura de la alerta disparada y del mensaje en Discord o webhook.site.

---

## 10. Demostración de los criterios de aceptación (hazla en clase)

### Criterio 1: commit con error → se bloquea el despliegue

**Error en un componente visual.** En `frontend/public/index.html` cambia el texto del botón:
```html
<button type="submit" class="btn primary" data-testid="login-submit">Entrar</button>
```
por `Ingresar`. **O un error en un endpoint:** en `backend/app/users.py`, en `create_user`, cambia
`return jsonify(user=_serialize(row)), 201` por `..., 200`.

```bash
git commit -am "demo: error intencional"
git push
```

Resultado esperado:
- **Actions:** el job *Pruebas* sale en rojo (falla Playwright y, en el caso del endpoint, también pytest).
- El job **Despliegue en AWS EC2** aparece como *skipped*: nunca se abrió la conexión SSH.
- El job **Despliegue bloqueado** sale en verde y registra el evento `deploy_blocked`.
- **OpenObserve** → stream `cicd_pipeline`: aparece `tests / failure` y `deploy_blocked / blocked`, con commit, rama y usuario.

### Criterio 2: commit válido → se despliega

Deshaz el cambio (`git revert HEAD` o corrígelo a mano), haz commit y push. Resultado esperado:
- Todo en verde. El job de deploy actualiza los contenedores en la EC2.
- En `cicd_pipeline` aparecen `tests / success` y `deploy / success`.
- `http://TU_IP/api/health` muestra la nueva `version` (los primeros 7 caracteres del commit).

### Criterio 3: vista simultánea

Abre el dashboard del paso 8 con los paneles de pipeline, trazas e infraestructura juntos.

---

## 11. Nota importante sobre la TEMPERATURA

Las instancias EC2 normales (t3, t2, m5…) son **máquinas virtuales**. El hipervisor de AWS **no expone los
sensores de temperatura** del procesador físico. Ninguna herramienta (lm-sensors, node_exporter ni el OTel Collector) puede leerla.
El agente **sí intenta leerla** (`/sys/class/thermal` y `/sys/class/hwmon`):
- Si la instancia expone algún sensor, la gráfica muestra los °C reales.
- Si no, el campo `temp_source` dice `sin_sensor_expuesto_por_hipervisor` y la gráfica queda vacía.

Puedes comprobarlo en la EC2 con `sensors` y con `ls /sys/class/thermal/`. Ambos saldrán vacíos.
**Ponlo en el reporte** como limitación técnica justificada, con captura del panel y de `sensors`. No se inventan datos.
Pregúntale a tu profe si con esa justificación es suficiente. La única forma de tener temperatura real es una
instancia *bare metal* (`*.metal`), que es muy cara.

---

## 12. Capturas para el reporte (figuras numeradas)

1. Diagrama de arquitectura (está en el reporte).
2. Repositorio en GitHub (estructura de carpetas).
3. Secrets configurados (solo los nombres, nunca los valores).
4. Instancia EC2 corriendo + Security Group.
5. `docker compose --profile monitoring ps` en la EC2.
6. Login de la app.
7. CRUD: lista, crear, editar y eliminar.
8. Resultado de pytest, Jest y Playwright en Actions (o el reporte HTML de Playwright, que está en *Artifacts*).
9. Pipeline en rojo con el deploy en *skipped* (criterio 1).
10. Pipeline en verde con el deploy exitoso (criterio 2).
11. OpenObserve: stream `cicd_pipeline` con eventos de éxito y fallo.
12. OpenObserve: logs estructurados de la app.
13. OpenObserve: traza con spans HTTP y SQL.
14. Dashboard de la aplicación (req/s, latencia, errores, statusCode).
15. Dashboard de infraestructura (CPU, RAM, red y temperatura).
16. Vista simultánea (criterio 3).
17. Alertas configuradas y una alerta disparada.

---

## 13. Al terminar

- Llena el reporte (`Reporte_Parcial2.docx`): portada institucional, links (repo, `http://TU_IP`, `http://TU_IP:5080`),
  credenciales de la app y de OpenObserve, y las figuras.
- **Después de la revisión, detén la instancia EC2** (*Instance state → Stop*) para que no te cobren.
  Si liberas la Elastic IP, hazlo solo después de terminar la instancia.

## Ejecutar todo en tu computadora (opcional)

```bash
cp .env.example .env && sed -i 's/OTEL_ENABLED=true/OTEL_ENABLED=false/; s/WEB_PORT=80/WEB_PORT=8080/' .env
docker compose up -d --build db backend frontend        # app en http://localhost:8080
cd backend && pip install -r requirements-dev.txt && pytest
cd ../frontend && npm install && npm test
cd ../e2e && npm install && npx playwright install chromium && npx playwright test
```
