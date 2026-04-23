# Архитектура MeetingAssistant

## Обзор системы

MeetingAssistant — корпоративная on-premise система для автоматической обработки записей совещаний. Разработана для банковского сектора с учётом требований информационной безопасности: все компоненты работают внутри корпоративного контура, внешние API не используются.

---

## Архитектурная схема

```
                        ┌─────────────────────────────────┐
                        │         Пользователи             │
                        │  Руководители / Секретари        │
                        └──────────────┬──────────────────┘
                                       │ HTTPS / WSS
                        ┌──────────────▼──────────────────┐
                        │           Nginx                  │
                        │    Reverse Proxy + TLS           │
                        └──────┬──────────────┬────────────┘
                               │              │
              ┌────────────────▼──┐    ┌──────▼──────────────┐
              │  Frontend (React)  │    │   Backend (FastAPI)  │
              │  Port 3000/80      │    │   Port 8000          │
              │                   │    │                       │
              │  - Dashboard       │    │  REST API v1          │
              │  - Upload          │    │  WebSocket /ws        │
              │  - Transcript view │    │  OpenAPI docs         │
              │  - Protocol editor │    │                       │
              │  - Tasks board     │    └──┬────────────────┬──┘
              │  - Analytics       │       │                │
              └───────────────────┘       │                │
                                   ┌──────▼─────┐   ┌──────▼──────┐
                                   │ PostgreSQL  │   │    Redis     │
                                   │ (основные   │   │  Pub/Sub +  │
                                   │  данные)    │   │  Task Queue │
                                   └────────────┘   └──────┬──────┘
                                                           │
                                                    ┌──────▼──────┐
                                                    │Celery Worker│
                                                    │             │
                                                    │ ┌─────────┐ │
                                                    │ │ Whisper │ │
                                                    │ │(local)  │ │
                                                    │ └─────────┘ │
                                                    │ ┌─────────┐ │
                                                    │ │pyannote │ │
                                                    │ │(diariz.)│ │
                                                    │ └─────────┘ │
                                                    │ ┌─────────┐ │
                                                    │ │ spaCy / │ │
                                                    │ │KeyBERT  │ │
                                                    │ └─────────┘ │
                                                    │ ┌─────────┐ │
                                                    │ │ Ollama  │ │
                                                    │ │(LLM)    │ │
                                                    │ └─────────┘ │
                                                    └──────┬──────┘
                                                           │
                                                    ┌──────▼──────┐
                                                    │    MinIO     │
                                                    │(аудио, DOCX)│
                                                    └────────────┘
```

---

## Поток обработки записи

```
Загрузка файла (audio/video)
         │
         ▼
  MinIO (хранение)
         │
         ▼
  Celery Task Queue
         │
         ├─ 1. Извлечение аудио (ffmpeg)
         │
         ├─ 2. Транскрибация (Whisper large-v3)
         │      ← WER < 10% на русском языке
         │
         ├─ 3. Диаризация спикеров (pyannote.audio)
         │      ← Разметка SPEAKER_00, SPEAKER_01...
         │
         ├─ 4. NLP-анализ
         │      ├─ Ключевые слова (KeyBERT + YAKE)
         │      ├─ Контакты (spaCy NER + regex)
         │      └─ Сентимент (Dostoevsky, рус. модель)
         │
         ├─ 5. Генерация саммари (LLM via Ollama)
         │
         ├─ 6. Генерация протокола (LLM + Jinja2 шаблон)
         │
         ├─ 7. Извлечение задач/поручений (LLM → JSON)
         │
         └─ 8. Сохранение в PostgreSQL
                + Уведомление по WebSocket (Redis Pub/Sub)
```

---

## Компоненты и ответственности

### Backend (FastAPI)

| Модуль | Назначение |
|--------|-----------|
| `api/auth.py` | JWT аутентификация, поддержка LDAP/AD |
| `api/meetings.py` | Загрузка файлов, CRUD совещаний |
| `api/transcriptions.py` | Чтение транскрипций, разметка участников |
| `api/protocols.py` | CRUD протокола, экспорт DOCX |
| `api/tasks.py` | Управление задачами, синхронизация Jira |
| `api/analytics.py` | Сентимент, ключевые слова, контакты, дашборд |
| `api/ws.py` | WebSocket — прогресс обработки в реальном времени |
| `services/transcription.py` | Whisper + pyannote диаризация |
| `services/nlp.py` | KeyBERT, YAKE, spaCy NER, Dostoevsky |
| `services/llm.py` | Клиент Ollama/OpenAI — саммари, протокол, задачи |
| `services/pipeline.py` | Celery-пайплайн — оркестрация всех шагов |
| `services/storage.py` | MinIO — загрузка/скачивание файлов |
| `services/jira_integration.py` | Опциональная интеграция с Jira |
| `services/ldap_auth.py` | Аутентификация через корпоративный AD |

### Frontend (React 18 + TypeScript)

| Страница/Компонент | Назначение |
|-------------------|-----------|
| `LoginPage` | Форма входа |
| `DashboardPage` | Статистика, последние совещания |
| `MeetingsPage` | Список всех совещаний |
| `UploadPage` | Загрузка файлов drag-and-drop |
| `MeetingDetailPage` | Детали совещания (4 вкладки) |
| `TranscriptView` | Транскрипция с поиском, спикерами |
| `ProtocolView` | Markdown-редактор протокола + экспорт |
| `TasksView` | Доска задач, статусы, Jira-синк |
| `AnalyticsView` | Графики: сентимент, ключевые слова, контакты |
| `ProcessingProgress` | Реалтайм-прогресс via WebSocket |

---

## Модели данных

```
User ──────────────┐
  id (UUID)        │  owns
  email            │
  full_name        ▼
  role          Meeting ─────────────────────────────────┐
                  id (UUID)                               │
                  title                             has one
                  status (enum)                          │
                  audio_object_key (MinIO)         ┌─────▼──────┐
                  video_object_key (MinIO)         │ Transcript  │
                  celery_task_id                   │  raw_text   │
                         │                         │  segments[] │
                    has many                       │  summary    │
                         │                         │  keywords[] │
               ┌─────────┼──────────┐              │  contacts[] │
               ▼         ▼          ▼              │  sentiment  │
         Protocol    MeetingTask  Participant      └────────────┘
         content_md  title        speaker_label
         agenda[]    assignee     display_name
         decisions[] due_date     role_in_meeting
                     jira_key
```

---

## Безопасность

- **JWT** (HS256) — короткоживущие access tokens (60 мин) + refresh tokens (7 дней)
- **LDAP/AD** — опциональная интеграция с корпоративным каталогом
- **HTTPS/TLS** — Nginx reverse proxy
- **MinIO** — пресайнед URLs для временного доступа к файлам
- **Изоляция сети** — все сервисы в Docker-сети / K8s namespace
- **Авторизация** — владелец совещания или admin

---

## KPI и метрики качества

| Метрика | Целевое значение | Инструмент измерения |
|---------|-----------------|---------------------|
| Word Error Rate (транскрипция) | < 10% | Whisper large-v3 benchmark |
| Точность разметки спикеров | > 85% DER | pyannote evaluation |
| ROUGE-L (саммари) | > 0.45 | rouge-score |
| Precision (задачи) | > 80% | Ручная разметка |
| Recall (задачи) | > 75% | Ручная разметка |
| Время обработки | < 0.3x длины записи | Celery task metrics |
| Аптайм API | > 99.5% | /health endpoint + мониторинг |

---

## Развёртывание (on-premise)

### Минимальные требования

| Компонент | CPU | RAM | Диск |
|-----------|-----|-----|------|
| Backend API (×2) | 4 cores | 8 GB | 20 GB |
| Celery Worker (×2) | 8 cores | 16 GB | 50 GB (модели) |
| PostgreSQL | 2 cores | 4 GB | 100 GB |
| MinIO | 2 cores | 4 GB | 2 TB+ |
| Ollama (LLM) | 8 cores | 16 GB | 50 GB |
| Redis | 1 core | 2 GB | 10 GB |

> **GPU опционально**: с NVIDIA GPU (16GB VRAM) время обработки 1ч записи сокращается с ~18 мин до ~3 мин.

### Способы развёртывания

1. **Docker Compose** — `make up` (dev/pilot)
2. **Kubernetes** — манифесты в `infra/k8s/` (production)
3. **Bare metal** — каждый сервис отдельным systemd-юнитом

---

## Интеграции

| Система | Статус | Описание |
|---------|--------|----------|
| **Jira** | Опционально | Автоматическое создание задач |
| **LDAP/AD** | Опционально | Единый вход (SSO) |
| **ВКС (Zoom/Webex)** | Roadmap | Запись «в прямом эфире» |
| **Корпоративный портал** | Roadmap | Embed-виджет протокола |
