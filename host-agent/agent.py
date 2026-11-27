"""Agente de recursos del servidor EC2 -> OpenObserve (API HTTP/JSON).

Cada INTERVAL segundos mide CPU, RAM, ancho de banda (red), disco, carga y
temperatura, y envia un registro JSON al stream O2_STREAM de OpenObserve.
Solo usa la libreria estandar de Python (lee /proc y /sys del host).
"""
import base64
import glob
import json
import os
import socket
import sys
import time
import urllib.request

O2_URL = os.getenv("O2_URL", "http://localhost:5080").rstrip("/")
O2_ORG = os.getenv("O2_ORG", "default")
O2_STREAM = os.getenv("O2_STREAM", "ec2_host_metrics")
O2_USER = os.getenv("O2_USER", "")
O2_PASSWORD = os.getenv("O2_PASSWORD", "")
INTERVAL = float(os.getenv("INTERVAL", "10"))
HOST_NAME = os.getenv("HOST_NAME") or socket.gethostname()
PROC = os.getenv("PROC_PATH", "/proc")
SYS = os.getenv("SYS_PATH", "/sys")
DISK_PATH = os.getenv("DISK_PATH", "/hostfs")
SKIP_IFACES = ("lo", "docker", "veth", "br-", "virbr")


def log(msg, **kw):
    print(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "msg": msg, **kw}), flush=True)


def read_cpu():
    with open(f"{PROC}/stat") as f:
        parts = [int(x) for x in f.readline().split()[1:]]
    idle = parts[3] + (parts[4] if len(parts) > 4 else 0)  # idle + iowait
    return idle, sum(parts)


def read_mem():
    info = {}
    with open(f"{PROC}/meminfo") as f:
        for line in f:
            key, val = line.split(":", 1)
            info[key] = int(val.split()[0])  # kB
    total = info["MemTotal"]
    available = info.get("MemAvailable", info.get("MemFree", 0))
    used = total - available
    return {
        "mem_total_mb": round(total / 1024, 1),
        "mem_used_mb": round(used / 1024, 1),
        "mem_percent": round(used * 100 / total, 2),
    }


def read_net():
    rx = tx = 0
    with open(f"{PROC}/net/dev") as f:
        for line in f.readlines()[2:]:
            iface, data = line.split(":", 1)
            iface = iface.strip()
            if iface.startswith(SKIP_IFACES):
                continue
            cols = data.split()
            rx += int(cols[0])
            tx += int(cols[8])
    return rx, tx


def read_disk():
    path = DISK_PATH if os.path.exists(DISK_PATH) else "/"
    st = os.statvfs(path)
    total = st.f_blocks * st.f_frsize
    free = st.f_bavail * st.f_frsize
    return round((total - free) * 100 / total, 2) if total else None


def read_load():
    with open(f"{PROC}/loadavg") as f:
        return float(f.read().split()[0])


def read_temperature():
    """Devuelve (temp_c_maxima, fuente) o (None, motivo)."""
    readings = []
    for zone in glob.glob(f"{SYS}/class/thermal/thermal_zone*"):
        try:
            with open(f"{zone}/temp") as f:
                value = int(f.read().strip()) / 1000
            with open(f"{zone}/type") as f:
                name = f.read().strip()
            readings.append((value, f"thermal:{name}"))
        except (OSError, ValueError):
            continue
    for sensor in glob.glob(f"{SYS}/class/hwmon/hwmon*/temp*_input"):
        try:
            with open(sensor) as f:
                value = int(f.read().strip()) / 1000
            name_file = os.path.join(os.path.dirname(sensor), "name")
            name = open(name_file).read().strip() if os.path.exists(name_file) else "hwmon"
            readings.append((value, f"hwmon:{name}"))
        except (OSError, ValueError):
            continue
    readings = [r for r in readings if -20 < r[0] < 150]
    if not readings:
        return None, "sin_sensor_expuesto_por_hipervisor"
    return max(readings)


def send(records):
    url = f"{O2_URL}/api/{O2_ORG}/{O2_STREAM}/_json"
    token = base64.b64encode(f"{O2_USER}:{O2_PASSWORD}".encode()).decode()
    req = urllib.request.Request(
        url,
        data=json.dumps(records).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Basic {token}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return res.status


def main(iterations=None):
    log("host-agent iniciado", url=O2_URL, stream=O2_STREAM, interval=INTERVAL)
    prev_idle, prev_total = read_cpu()
    prev_rx, prev_tx = read_net()
    prev_t = time.time()
    count = 0
    while iterations is None or count < iterations:
        time.sleep(INTERVAL)
        idle, total = read_cpu()
        rx, tx = read_net()
        now = time.time()
        dt = max(now - prev_t, 1e-6)
        d_total = total - prev_total
        cpu = round((1 - (idle - prev_idle) / d_total) * 100, 2) if d_total else 0.0
        temp, temp_source = read_temperature()

        record = {
            "host": HOST_NAME,
            "cpu_percent": cpu,
            **read_mem(),
            "net_rx_kbps": round((rx - prev_rx) * 8 / 1000 / dt, 2),
            "net_tx_kbps": round((tx - prev_tx) * 8 / 1000 / dt, 2),
            "net_rx_bytes_total": rx,
            "net_tx_bytes_total": tx,
            "disk_percent": read_disk(),
            "load1": read_load(),
            "temp_source": temp_source,
        }
        if temp is not None:
            record["temp_c"] = round(temp, 1)

        try:
            send([record])
        except Exception as exc:  # no detenemos el agente si OpenObserve no responde
            log("error enviando a OpenObserve", error=str(exc))
        else:
            log("metricas enviadas", **record)

        prev_idle, prev_total, prev_rx, prev_tx, prev_t = idle, total, rx, tx, now
        count += 1


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
