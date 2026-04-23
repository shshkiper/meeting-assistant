# Руководство по развёртыванию

## 1. Быстрый старт (Docker Compose)

```bash
# Клонировать репозиторий
git clone https://github.com/CodeIS/meeting-assistant.git
cd meeting-assistant

# Создать .env
cp .env.example .env
# Обязательно смените SECRET_KEY в .env!

# Первичная настройка (запускает БД, Redis, MinIO, Ollama, миграции)
make setup

# Запустить все сервисы
make up

# Открыть интерфейс
open http://localhost:3000
```

### После запуска

| Сервис | URL | Описание |
|--------|-----|----------|
| Frontend | http://localhost:3000 | Веб-интерфейс |
| Backend API | http://localhost:8000/api/docs | Swagger UI |
| MinIO Console | http://localhost:9001 | Управление файлами |
| Flower | http://localhost:5555 | Мониторинг очереди |

---

## 2. Первый пользователь

После старта зарегистрируйте администратора:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@bank.com",
    "full_name": "Администратор",
    "password": "StrongPass123!",
    "role": "admin"
  }'
```

---

## 3. Загрузка LLM-модели (Ollama)

```bash
# Загрузить модель llama3.1:8b (по умолчанию)
make ollama-pull

# Или другую модель (mistral, qwen2 и т.д.)
docker compose exec ollama ollama pull mistral:7b

# Обновить LLM_MODEL в .env
LLM_MODEL=mistral:7b
```

---

## 4. Production (Kubernetes)

```bash
# Применить манифесты
kubectl apply -f infra/k8s/deployment.yaml

# Проверить статус
kubectl get pods -n meeting-assistant

# Логи бэкенда
kubectl logs -n meeting-assistant deploy/backend -f

# Логи воркера
kubectl logs -n meeting-assistant deploy/worker -f
```

### Secrets в K8s

Перед деплоем создайте secrets:

```bash
kubectl create secret generic meeting-assistant-secrets \
  --namespace meeting-assistant \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=DATABASE_URL="postgresql+asyncpg://..." \
  --from-literal=REDIS_URL="redis://..." \
  --from-literal=MINIO_ACCESS_KEY="..." \
  --from-literal=MINIO_SECRET_KEY="..."
```

---

## 5. LDAP/AD интеграция

```env
# .env
LDAP_ENABLED=true
LDAP_SERVER=ldap://dc01.bank.local
LDAP_BASE_DN=dc=bank,dc=local
LDAP_BIND_DN=cn=svc_meeting,ou=ServiceAccounts,dc=bank,dc=local
LDAP_BIND_PASSWORD=YourServiceAccountPassword
```

После включения пользователи могут входить через корпоративные учётные данные.

---

## 6. Jira интеграция

```env
# .env
JIRA_ENABLED=true
JIRA_URL=https://jira.bank.local
JIRA_TOKEN=your-personal-access-token
JIRA_PROJECT_KEY=MTG
```

Получить token: Jira → Profile → Personal Access Tokens

---

## 7. GPU-ускорение (опционально)

Для ускорения транскрибации с NVIDIA GPU:

```env
# .env
WHISPER_DEVICE=cuda
```

```yaml
# docker-compose.yml — раскомментировать в секции worker:
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

---

## 8. Мониторинг и обслуживание

```bash
# Логи в реальном времени
make logs

# Статус всех контейнеров
docker compose ps

# Перезапуск воркера после обновления кода
docker compose restart worker

# Очистка устаревших задач Celery
docker compose exec worker celery -A app.services.pipeline.celery_app purge

# Бэкап PostgreSQL
docker compose exec postgres pg_dump -U meetinguser meetingdb > backup_$(date +%Y%m%d).sql
```
