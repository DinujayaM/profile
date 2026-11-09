# 🌟 TinyTales World – AI-Powered Kids Video Platform

An automated, AI-powered platform that researches, produces, and publishes original children's
educational and entertainment videos to YouTube. Built with a focus on originality — never
copying existing shows like Cocomelon or Pinkfong.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      TinyTales World                            │
├──────────────┬───────────────────────┬──────────────────────────┤
│   Frontend   │       Backend          │     Background Workers   │
│  React/Vite  │   FastAPI + Python    │   Celery + Redis         │
│  Ant Design  │   PostgreSQL           │   Scheduled Tasks        │
│  Recharts    │   SQLAlchemy           │   Video Pipeline         │
└──────────────┴───────────────────────┴──────────────────────────┘
                           │
         ┌─────────────────┼─────────────────────┐
         │                 │                     │
    AI Providers     YouTube API          Cloud Storage
    (LLM/Image/      (OAuth2 upload,       (S3/GCS/Local)
    Video/TTS/Music)  analytics)
```

## Production Pipeline (15 Steps)

1. ✅ Select approved video idea
2. ✅ Generate original script (LLM)
3. ✅ Generate scene-by-scene storyboard (LLM)
4. ✅ Generate character images (Image AI)
5. ✅ Animate scenes as video clips (Video AI)
6. ✅ Generate voiceover / narration (TTS)
7. ✅ Generate original background music (Music AI)
8. ✅ Generate subtitles
9. ✅ Render final video (FFmpeg)
10. ✅ Mix audio tracks
11. ✅ Generate thumbnail (Image AI)
12. ✅ Run quality checks
13. ✅ Save to cloud storage
14. ✅ Send for admin approval
15. ✅ Upload approved video to YouTube

## Quick Start (Development)

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your values

# 2. Start all services
docker-compose up -d

# 3. Access the admin portal
open http://localhost
```

The first registered user becomes superadmin automatically.

## Development (Without Docker)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start API server
uvicorn app.main:app --reload --port 8000

# Start Celery worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Run migrations
alembic upgrade head
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## AI Provider Configuration

All providers are configurable via environment variables. The platform ships with
**mock providers** that return realistic-looking responses for development.

| Service | Providers Supported | Env Var |
|---------|--------------------|---------| 
| LLM | OpenAI, Anthropic, mock | `LLM_PROVIDER` |
| Images | OpenAI DALL-E, Stability AI, mock | `IMAGE_PROVIDER` |
| Video clips | Runway, Pika, mock | `VIDEO_PROVIDER` |
| Text-to-speech | ElevenLabs, Google TTS, mock | `TTS_PROVIDER` |
| Music | Suno, Udio, mock | `MUSIC_PROVIDER` |
| Storage | S3, GCS, local | `STORAGE_PROVIDER` |

To activate a provider, set the provider name and its API key:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

## Admin Portal Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/dashboard` | KPI stats, cost tracking, recent videos |
| AI Research | `/research` | Generate and manage video ideas |
| Video Ideas | `/ideas` | Browse all ideas with status |
| Script Generator | `/scripts` | View and approve generated scripts |
| Storyboard Editor | `/storyboards` | Visual scene editor |
| Character Library | `/characters` | Manage original characters |
| Audio Library | `/audio` | Voiceovers, music assets |
| Video Production | `/production` | Start and monitor production pipeline |
| Approval Queue | `/approval` | Approve/reject completed videos |
| YouTube Upload | `/youtube` | OAuth, upload scheduling |
| Analytics | `/analytics` | Performance charts and cost tracking |
| Settings | `/settings` | API config, cost limits |

## Security

- JWT authentication (access + refresh tokens)
- bcrypt password hashing
- Role-based access control (viewer / editor / admin / superadmin)
- Rate limiting on API and auth endpoints
- SQL injection prevention via SQLAlchemy ORM
- XSS protection via security headers
- All secrets via environment variables — never committed
- Audit logging for all admin actions
- OAuth tokens encrypted at rest

## Project Structure

```
tinytales-world/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # REST API endpoints
│   │   ├── core/             # Config, DB, security
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   │   └── ai/           # AI provider adapters
│   │   └── workers/          # Celery tasks
│   ├── alembic/              # Database migrations
│   └── tests/                # pytest tests
├── frontend/
│   └── src/
│       ├── api/              # Axios API client
│       ├── components/       # Reusable components
│       ├── pages/            # Page components
│       ├── store/            # Zustand state management
│       └── types/            # TypeScript types
├── nginx/                    # Reverse proxy config
├── .github/workflows/        # CI/CD (GitHub Actions)
├── docker-compose.yml        # Production compose
└── .env.example              # Environment template
```

## Development Phases

- [x] **Phase 1** – System architecture
- [x] **Phase 2** – Database models and backend foundation
- [x] **Phase 3** – Frontend dashboard and authentication
- [x] **Phase 4** – AI research and script generation
- [x] **Phase 5** – Character and storyboard management
- [ ] **Phase 6** – Full AI provider integrations (requires API keys)
- [ ] **Phase 7** – Complete FFmpeg rendering pipeline
- [ ] **Phase 8** – YouTube OAuth and publishing
- [ ] **Phase 9** – Analytics and cost management
- [ ] **Phase 10** – Security hardening and production deployment

## Content Policy

This platform generates **original** children's content only:
- No copying of characters, songs, scripts, or branding from existing shows
- All content is Made for Kids (YouTube classification)
- Safety review step in the pipeline before approval
- Administrator approval required before any video is published
