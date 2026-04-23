# 🎙️ MeetingAssistant — Цифровой ассистент для обработки совещаний

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)

Корпоративная on-premise система для автоматической обработки записей совещаний: транскрибация, разметка ролей, генерация протоколов, постановка задач.

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  Upload → Transcript View → Protocol → Tasks Dashboard          │
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST API / WebSocket
┌─────────────────────────▼───────────────────────────────────────┐
│                    BACKEND (FastAPI)                             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Transcription│  │   NLP / AI   │  │  Protocol Generator  │  │
│  │   Service    │  │   Pipeline   │  │     Service          │  │
│  │  (Whisper)   │  │ (Roles/Tasks)│  │  (LLM + Template)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Sentiment   │  │   Keywords   │  │   Task Manager       │  │
│  │  Analysis    │  │  Extraction  │  │   (Jira/Portal)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────┬────────────────────────────────────┬─────────────┘
              │                                    │
┌─────────────▼──────────┐          ┌─────────────▼──────────────┐
│   PostgreSQL + Redis   │          │   MinIO (File Storage)      │
│   (Data + Cache/Queue) │          │   (Audio/Video/Docs)        │
└────────────────────────┘          └────────────────────────────┘
```

## 🚀 Возможности

| Функция | Описание |
|---|---|
| 🎙️ **Транскрибация** | Whisper (local) — точная транскрибация аудио/видео записей |
| 👤 **Разметка ролей** | Диаризация спикеров + сопоставление с корпоративной базой |
| 📄 **Протокол** | Автогенерация протокола по корпоративному стандарту |
| ✅ **Задачи** | Извлечение action items и постановка задач |
| 💬 **Саммари** | Краткое резюме встречи с ключевыми решениями |
| 📊 **Сентимент-анализ** | Базовый и продвинутый анализ тональности |
| 🔑 **Ключевые слова** | Извлечение терминов и ключевых тем |
| 📇 **Контакты** | Автоматическое извлечение упомянутых контактов |

## 📦 Стек технологий

### Backend
- **FastAPI** — REST API + WebSocket
- **OpenAI Whisper** — транскрибация (local, on-premise)
- **pyannote.audio** — диаризация спикеров
- **spaCy / transformers** — NLP pipeline
- **Celery + Redis** — очередь задач
- **PostgreSQL** — хранение данных
- **MinIO** — объектное хранилище файлов
- **SQLAlchemy** — ORM

### Frontend
- **React 18** + TypeScript
- **Zustand** — state management
- **TanStack Query** — data fetching
- **Tailwind CSS** — стили
- **shadcn/ui** — компоненты

### Инфраструктура
- **Docker Compose** — локальное развёртывание
- **Nginx** — reverse proxy
- **Kubernetes** — production (манифесты включены)

## ⚡ Быстрый старт

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/CodeIS/meeting-assistant.git
cd meeting-assistant

# 2. Скопируйте конфигурацию
cp .env.example .env
# Отредактируйте .env под ваше окружение

# 3. Запустите через Docker Compose
docker compose up -d

# 4. Откройте браузер
open http://localhost:3000
```

## 📁 Структура проекта

```
meeting-assistant/
├── backend/              # FastAPI приложение
│   ├── app/
│   │   ├── api/          # Роутеры (endpoints)
│   │   ├── core/         # Конфигурация, безопасность
│   │   ├── services/     # Бизнес-логика
│   │   ├── models/       # SQLAlchemy модели
│   │   └── schemas/      # Pydantic схемы
│   └── tests/            # Тесты
├── frontend/             # React приложение
│   └── src/
│       ├── components/   # UI компоненты
│       ├── pages/        # Страницы
│       ├── store/        # Zustand store
│       └── hooks/        # React hooks
├── infra/                # Инфраструктура
│   ├── docker/           # Dockerfiles
│   ├── nginx/            # Nginx конфиг
│   └── k8s/              # Kubernetes манифесты
├── docs/                 # Документация
└── scripts/              # Утилиты
```

## 📋 KPI системы

- **Точность транскрибации**: WER < 10% на русскоязычных записях
- **Точность разметки ролей**: > 85% совпадение с ручной разметкой
- **Качество саммари**: ROUGE-L > 0.45
- **Извлечение задач**: Precision > 80%, Recall > 75%
- **Время обработки**: < 0.3x от длины записи (1 час → < 18 минут)

## 📄 Лицензия

MIT — см. [LICENSE](LICENSE)
