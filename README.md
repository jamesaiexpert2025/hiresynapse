# HireSynapse — Agentic AI CEO Monorepo (Starter)

This repo lets you deploy **without running anything locally**:

- **Render**: deploys the backend API (FastAPI).
- **Vercel**: deploys the website (React/Vite).
- **GitHub**: stores your code and lets the Agentic AI CEO open Pull Requests for test builds.

## What’s inside
- `apps/api` → backend (auth + Agent CEO + GitHub PR integration)
- `apps/web` → frontend (login + CEO Console)
- `.github/workflows/preview.yml` → builds on pull requests

## Quick Deploy
1) Push this repo to GitHub.
2) **Render** → New Web Service → Root Directory = `apps/api` → set env vars (see below) → Deploy.
3) **Vercel** → New Project → Root Directory = `apps/web` → set env `VITE_API_URL` to your Render URL → Deploy.

## Backend ENV (Render)
- `AUTH_SECRET` = long random string
- `ADMIN_EMAIL` = your admin login email (Master Admin)
- `ADMIN_PASSWORD` = your admin password
- `AI_CEO_EMAIL` = AI CEO login email (e.g., ceo@hiresynapse.ai)
- `AI_CEO_PASSWORD` = AI CEO password
- `GITHUB_OWNER` = your GitHub username/org (e.g., jamesaiexpert)
- `GITHUB_REPO` = repo name (e.g., hiresynapse)
- `GITHUB_TOKEN` = GitHub Fine-grained token with repo read/write + PR read/write
- (Optional) `DATABASE_URL` = Postgres URL (if not set, uses SQLite file)

## Frontend ENV (Vercel)
- `VITE_API_URL` = https://<your-render-service>.onrender.com
- (Optional) `VITE_GH_OWNER` and `VITE_GH_REPO` for PR links in the console

## Flow
1. AI CEO proposes an idea in the Console.
2. You (Admin) approve.
3. AI CEO executes → opens a GitHub Pull Request with changes.
4. PR triggers preview build (Vercel). You test.
5. You merge when satisfied (final authority stays with you).
