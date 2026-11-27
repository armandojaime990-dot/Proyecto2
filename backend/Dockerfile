FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY wsgi.py .
EXPOSE 5000
# Cada worker de gunicorn inicializa su propio OpenTelemetry (sin --preload)
CMD ["gunicorn", "-w", "2", "--threads", "4", "-b", "0.0.0.0:5000", "--access-logfile", "-", "wsgi:app"]
