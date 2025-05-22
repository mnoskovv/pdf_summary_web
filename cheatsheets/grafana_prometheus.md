# 🔧 Monitoring Cheatsheet (Django + Prometheus + Grafana)

## 🐍 Django

### Что добавили в Django

1. Установили зависимости:
   ```bash
   pip install prometheus_client django-prometheus
   ```

2. В `settings.py`:
   ```python
   INSTALLED_APPS = [
       'django_prometheus',
       ...
   ]

   MIDDLEWARE = [
       'django_prometheus.middleware.PrometheusBeforeMiddleware',
       ...
       'django_prometheus.middleware.PrometheusAfterMiddleware',
   ]
   ```

3. В `urls.py`:
   ```python
   from django_prometheus import exports

   urlpatterns += [path("metrics", exports.ExportToDjangoViewMiddleware)]
   ```

---

## 🐳 Docker Compose

В `docker-compose.yml`:
```yaml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  django:
    build: .
    ports:
      - "8000:8000"
```

---

## 📈 Пример кастомной метрики

```python
from prometheus_client import Counter

my_counter = Counter("my_custom_counter", "Описание метрики")

def my_view(request):
    my_counter.inc()
    return HttpResponse("OK")
```

---

## 📊 Метрики Prometheus

- `Counter` — только увеличивается.
- `Gauge` — может увеличиваться и уменьшаться.
- `Histogram` — распределение значений по "корзинам".
- `Summary` — похож на `Histogram`, но дает квантильные оценки.

---

## 🐞 Проблемы и решения

- ❌ `connection refused`:
  - 🔧 Прометеус не мог достучаться до Django из контейнера.
  - ✅ Решение: заменить `localhost` на `host.docker.internal` в `prometheus.yml`:
    ```yaml
    static_configs:
      - targets: ['host.docker.internal:8000']
    ```

- ❌ Метрики не отображаются:
  - Проверить `/metrics` в браузере — если открывается, то проблема в Prometheus.
  - Проверить `targets` в Prometheus UI: http://localhost:9090/targets

---

## 📉 Grafana

- Установлена отдельно или через Docker.
- Подключили Prometheus как источник данных.
- Создали дашборд и график по метрике, например:
  ```promql
  django_http_requests_total
  ```

### Зачем нужна Grafana?
Для визуализации данных из Prometheus в виде графиков, панелей и алертов.