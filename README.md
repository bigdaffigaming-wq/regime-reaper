# ☠️ REGIME REAPER

**Asset Acquisition Intelligence System**

> Harvest Value. Reap Profit.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI + SQLite + SQLAlchemy |
| Frontend | React + Vite + Tailwind |
| Discord | discord.py slash commands |
| AI | OpenAI (gpt-4o-mini) |
| FB Scraping | Scrapfly |
| Port | Backend: 8093 / Frontend: 8094 |

---

## Quick Start

### 1. Backend

```bash
cd backend
cp .env.example .env
# Fill in OPENAI_API_KEY, SCRAPFLY_KEY, DISCORD_WEBHOOK_URL
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8093
```

### 2. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

### 3. Discord Bot

```bash
cd discord_bot
pip install -r requirements.txt
python bot.py
```

---

## Env Variables (backend/.env)

| Variable | Required | Description |
|---|---|---|
| OPENAI_API_KEY | No | LLM analysis (gpt-4o-mini) |
| SCRAPFLY_KEY | No | Facebook Marketplace search |
| DISCORD_BOT_TOKEN | No | Discord slash commands |
| DISCORD_WEBHOOK_URL | No | Deal alert webhooks |
| DISCORD_GUILD_ID | No | Guild for slash command sync |

All optional — REAPER runs without any of them, just with reduced features.

---

## Discord Commands

| Command | Description |
|---|---|
| `/reaper-search` | Search Facebook Marketplace |
| `/reaper-analyze` | Analyze a listing by ID or text |
| `/reaper-settings` | View current settings |
| `/reaper-set` | Update a setting |
| `/reaper-inventory` | View inventory |
| `/reaper-bought` | Mark listing as bought |
| `/reaper-sold` | Mark inventory item as sold |
| `/reaper-inspect` | Run interactive inspection checklist |

---

## Deal Verdicts

| Verdict | Criteria |
|---|---|
| BUY NOW | Score ≥ 85, Profit ≥ $1,500, Low/Medium risk |
| NEGOTIATE HARD | Score 70–84, Profit ≥ $1,000 |
| MONITOR | Score 55–69, Profit ≥ $500 |
| WALK AWAY | Score < 55, auto-reject flag, or extreme risk |

---

## Phase Map

- **Phase 1 (NOW):** Manual intake, Facebook via Scrapfly, scoring, profit math, inventory, Discord, dashboard
- **Phase 2:** Craigslist + Cars.com adapters, multi-source search
- **Phase 3:** Automated scheduled scanning
- **Phase 4:** Full Discord control parity
- **Phase 1.5:** REAPER VISION (photo condition analysis)
