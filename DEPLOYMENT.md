# Deploying TinyTales World (Free Tier)

**Stack:** Vercel (frontend) + Render (backend API) + Supabase (PostgreSQL) + Upstash (Redis)

---

## Step 1 — Supabase (Free PostgreSQL)

1. Go to https://supabase.com and sign up / log in.
2. Click **New project** → give it a name like `tinytales`.
3. Set a strong database password and save it.
4. Wait for the project to provision (~2 min).
5. Go to **Settings → Database → Connection string → URI**.
6. Copy the URI — it looks like:
   ```
   postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
   ```
7. **Important:** change the scheme to `postgresql+asyncpg://` for SQLAlchemy:
   ```
   postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
   ```
8. Save this — you'll need it in Step 3.

---

## Step 2 — Upstash (Free Redis)

1. Go to https://upstash.com and sign up / log in.
2. Click **Create Database** → choose **Redis** → region closest to you.
3. After creation, go to **Details** tab.
4. Copy the **Redis URL** — it starts with `rediss://` (TLS).
5. Save this — you'll need it in Step 3.

---

## Step 3 — Render (Free Backend API)

1. Go to https://render.com and sign up with your GitHub account.
2. Click **New → Blueprint** and connect your `DinujayaM/profile` repository.
3. Render will detect `render.yaml` automatically and show two services:
   - `tinytales-api` (web service)
   - `tinytales-frontend` (static site)
4. Before deploying, click on `tinytales-api` → **Environment** and add:

   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | The `postgresql+asyncpg://...` URL from Step 1 |
   | `REDIS_URL` | The `rediss://...` URL from Step 2 |
   | `CELERY_BROKER_URL` | Same as `REDIS_URL` |
   | `CELERY_RESULT_BACKEND` | Same as `REDIS_URL` |
   | `ALLOWED_ORIGINS` | `https://tinytales-world.vercel.app` (update after Step 4) |
   | `YOUTUBE_CLIENT_ID` | Your Google OAuth client ID (optional) |
   | `YOUTUBE_CLIENT_SECRET` | Your Google OAuth client secret (optional) |

5. Click **Apply** → Render will build and deploy.
6. After deploy, copy your API URL — it looks like:
   ```
   https://tinytales-api.onrender.com
   ```

> **Note:** Free Render web services sleep after 15 minutes of inactivity.
> The first request after sleep takes ~30 seconds to wake up.

---

## Step 4 — Vercel (Free Frontend)

1. Go to https://vercel.com and sign up with your GitHub account.
2. Click **Add New → Project** → import `DinujayaM/profile`.
3. Set the **Root Directory** to `frontend`.
4. Under **Environment Variables**, add:

   | Key | Value |
   |-----|-------|
   | `VITE_API_URL` | `https://tinytales-api.onrender.com/api/v1` |

5. Click **Deploy**.
6. After deploy, copy your Vercel URL — it looks like:
   ```
   https://tinytales-world.vercel.app
   ```
7. Go back to Render → `tinytales-api` → Environment → update `ALLOWED_ORIGINS` to your Vercel URL.

---

## Step 5 — First Login

1. Open your Vercel URL in the browser.
2. Click **Register** and create your admin account.
3. The **first registered user automatically becomes superadmin**.
4. You're in!

---

## Optional: Add AI Providers

Set these in Render → `tinytales-api` → Environment:

| Feature | Key | Where to get |
|---------|-----|-------------|
| LLM (scripts) | `OPENAI_API_KEY`, `LLM_PROVIDER=openai` | platform.openai.com |
| LLM (alternative) | `ANTHROPIC_API_KEY`, `LLM_PROVIDER=anthropic` | console.anthropic.com |
| Images | `STABILITY_API_KEY`, `IMAGE_PROVIDER=stability` | platform.stability.ai |
| Voiceover | `ELEVENLABS_API_KEY`, `TTS_PROVIDER=elevenlabs` | elevenlabs.io |
| YouTube | `YOUTUBE_CLIENT_ID` + `YOUTUBE_CLIENT_SECRET` | console.cloud.google.com |

Without API keys, the platform runs with **mock providers** — all features work but AI outputs are simulated.

---

## Free Tier Limits

| Service | Limit |
|---------|-------|
| Supabase | 500 MB database, 2 GB bandwidth/month |
| Upstash | 10,000 Redis commands/day |
| Render | 750 hours/month web service, sleeps after 15 min idle |
| Vercel | 100 GB bandwidth/month, unlimited static hosting |

---

## Upgrade Path (when you outgrow free)

- **Render** paid worker ($7/mo) → enables Celery background jobs (video rendering)
- **Supabase Pro** ($25/mo) → 8 GB database, no expiry
- **Cloudflare R2** (free 10 GB) → for video file storage (`STORAGE_PROVIDER=s3`)
