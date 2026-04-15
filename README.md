# hyper-track

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Hyperliquid](https://img.shields.io/badge/Hyperliquid-API-00C853)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

Perpetual futures wallet discovery and tracking engine for Hyperliquid.

On-chain perpetual trading is exploding -- Hyperliquid alone processes over $10B in daily volume with fully transparent order flow. But unlike spot wallets (tracked by Nansen, Arkham, etc.), tooling for tracking perp wallet performance barely exists. hyper-track discovers active traders through vault follower scanning, scores them on risk-adjusted metrics, classifies their trading style, and exposes everything through a live leaderboard and wallet detail dashboard.

<!-- ![Demo](demo.gif) -->

## Features

### Wallet Discovery

Scans Hyperliquid vault depositors to find active perp traders. The HLP vault (Hyperliquid's main market-making vault) has 100+ followers -- many are whales who also trade perps independently. The scanner checks each follower's fill history over 90 days and adds anyone with meaningful activity. Discovery can be triggered from the dashboard with a single click, or run as a script for batch processing.

### 10-Metric Scoring Engine

Every tracked wallet gets a composite score (0-100) computed from 9 weighted metrics across three rolling time windows (30-day, 90-day, all-time). The 90-day window drives the leaderboard ranking. Metrics include risk-adjusted returns (Sharpe, Sortino), capital efficiency (ROI, profit factor), consistency (win rate, reward-to-risk ratio), drawdown resilience, trade volume, and longevity. Raw fills are grouped into round-trip trades -- a trade opens when a position goes from zero to non-zero and closes when it returns to zero.

### Style Classification

Each wallet is automatically classified by trading style based on average hold time and trade frequency. A scalper holds under an hour with 10+ trades per day. A day trader operates within 24 hours. A swing trader holds for days. A position trader holds for weeks or longer. Additional tags capture behavioral patterns -- "sniper" for high-accuracy fast traders, "grinder" for volume-based edge, "concentrated" for single-asset specialists, "diversified" for broad portfolios.

### Interactive Dashboard

Dark-mode trading terminal UI with a sortable leaderboard, style filter tabs, and detailed wallet profiles. Click any wallet to see the full score breakdown across all three time windows, open positions with live mark prices, and recent fill history. The methodology modal explains every scoring weight and classification rule. Hover any metric label for an inline definition.

### Score Breakdown

Click any composite score to see exactly how it was calculated -- each of the 9 factors shows its raw value, normalized score, progress bar, and point contribution to the final number. No black boxes.

## How It Works

### Scoring Weights

| Metric | Weight | What It Measures | Cap |
|--------|--------|-----------------|-----|
| ROI | 15% | Return on time-weighted average capital | 500% |
| Sharpe Ratio | 15% | Return per unit of total risk (daily PnL volatility) | 5.0 |
| Max Drawdown | 15% | Largest peak-to-trough PnL decline (inverted -- lower is better) | 100% |
| Win Rate | 10% | Percentage of profitable round-trip trades | 100% |
| Sortino Ratio | 10% | Return per unit of downside risk only (ignores upside variance) | 8.0 |
| Profit Factor | 10% | Gross profits divided by gross losses | 5.0 |
| Trade Volume | 10% | Number of completed round-trip trades | 200 |
| Longevity | 10% | Days active on the platform | 180 |
| Reward:Risk | 5% | Average winning trade size divided by average losing trade size | 5.0 |

### Style Classification

| Style | Avg Hold Time | Trade Frequency |
|-------|--------------|----------------|
| Scalper | Under 1 hour | 10+ trades/day |
| Day Trader | Under 24 hours | 2-10 trades/day |
| Swing Trader | Under 7 days | Less than 2/day |
| Position Trader | Over 7 days | Very selective |

### Data Pipeline

```
Discovery (vault scan, submit, import)
         |
         v
    wallets table (Postgres)
         |
         v
    Poll Worker (async, priority queue)
     /         \
    v           v
userFillsByTime  clearinghouseState
     \           /
      v         v
  fills table   wallet_snapshots
         |
         v
    Score Worker (30min cycle)
         |
         v
    wallet_scores + leaderboard (materialized view)
         |
         v
    FastAPI (port 8003) --> Next.js (port 3004)
```

1. **Discover** -- Scan HLP vault followers, accept community submissions, or bulk import from CSV
2. **Backfill** -- New wallets get 90 days of historical fills via paginated `userFillsByTime`
3. **Poll** -- Active wallets polled on a priority schedule (hot: 2min, warm: 15min, cold: 1hr, frozen: 6hr)
4. **Score** -- Fills grouped into round-trip trades, 10 metrics computed per window, composite calculated
5. **Serve** -- Materialized leaderboard refreshed every 5 minutes, served via FastAPI to the Next.js dashboard

## Architecture

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, Tailwind v4, Lucide icons, Geist fonts |
| API | FastAPI, uvicorn |
| Data Layer | Python 3.11+, httpx (async), asyncpg |
| Database | PostgreSQL 17 (partitioned fills, materialized views) |
| Hyperliquid API | REST POST to `api.hyperliquid.xyz/info` |

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 17+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Install

```bash
git clone https://github.com/matthewrahm/hyper-track.git
cd hyper-track

# Python dependencies
uv sync

# Web dependencies
cd web && npm install && cd ..
```

### Configure

```bash
cp .env.example .env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (default: `postgresql://localhost/hyper_track`) |
| `HL_API_URL` | No | Hyperliquid API base URL (default: `https://api.hyperliquid.xyz`) |
| `POLL_CONCURRENCY` | No | Number of concurrent poll workers (default: 5) |
| `BACKFILL_DAYS` | No | Days of history to backfill for new wallets (default: 90) |
| `NEXT_PUBLIC_API_URL` | No | FastAPI URL for the frontend (default: `http://localhost:8003`) |

### Setup Database

```bash
createdb hyper_track
uv run python scripts/migrate.py
```

### Run

```bash
# Both servers
./scripts/dev.sh

# Or separately
uv run uvicorn api.main:app --reload --port 8003
cd web && npm run dev -- --port 3004

# Start the poll worker (backfills + scores wallets)
uv run python -m hyper_track.worker
```

Open http://localhost:3004

### Discover Wallets

From the dashboard, click "Scan HLP Vault" to discover active traders. Or run scripts directly:

```bash
# Scan vault followers
uv run python scripts/discover_vaults.py

# Import from file
uv run python scripts/import_addresses.py addresses.csv
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/leaderboard` | Ranked wallets with scores, sortable by any metric, filterable by style |
| `GET /api/wallet/{address}` | Wallet metadata (source, tier, status, fill count) |
| `GET /api/wallet/{address}/score` | Full score breakdown across all three time windows |
| `GET /api/wallet/{address}/fills` | Recent trade fills with pagination |
| `GET /api/wallet/{address}/snapshot` | Current positions, margin, and account value |
| `GET /api/wallet/{address}/history` | Score trend over time (for sparkline charts) |
| `POST /api/wallet` | Submit a new wallet address to track |
| `POST /api/discover/vaults` | Trigger vault follower scan for active traders |
| `GET /api/health` | Database connectivity and wallet counts |

## Project Structure

```
hyper-track/
  pyproject.toml                # Python dependencies
  migrations/
    001_initial.sql             # Tables, partitions (monthly fills)
    002_indexes.sql             # Query-path indexes
    003_materialized_views.sql  # Leaderboard view
  api/                          # FastAPI backend
    main.py                     # App, CORS, lifespan
    routes.py                   # REST endpoints + vault discovery
    schemas.py                  # Pydantic response models
  src/hyper_track/              # Core data layer
    client.py                   # Async Hyperliquid API client
    scorer.py                   # 10-metric scoring engine + style classification
    worker.py                   # Priority queue poll loop + backfill + scoring
    db.py                       # asyncpg connection pool + all queries
    models.py                   # Fill, Trade, WalletScore dataclasses
    config.py                   # Environment config
    cache.py                    # TTL cache
    seeds.py                    # Initial wallet addresses
  scripts/
    dev.sh                      # Run both servers
    migrate.py                  # Database migrations
    discover_vaults.py          # Scan HL vaults for active traders
    discover_leaderboard.py     # Curated trader addresses
    import_addresses.py         # Bulk import from CSV/JSON/TXT
  web/                          # Next.js dashboard
    app/
      page.tsx                  # Leaderboard + discovery panel
      wallet/[address]/page.tsx # Wallet detail page
      globals.css               # Design system tokens
      components/
        LeaderboardTable.tsx    # Sortable table with style filters
        DiscoverPanel.tsx       # One-click vault scanning
        MethodologyModal.tsx    # Scoring explanation modal
        ScoreBreakdown.tsx      # Clickable score factor breakdown
        Header.tsx              # Branding + methodology link
        AddressCell.tsx         # Truncated address with copy button
        ScoreBadge.tsx          # Color-coded score pill
        StyleBadge.tsx          # Trading style label
        NumberCell.tsx          # Formatted monospace numbers
        SubmitWallet.tsx        # Address submission form
        InfoTerm.tsx            # Hover tooltip for definitions
        Tooltip.tsx             # Portal-based tooltip
      hooks/
        useAutoRefresh.ts       # Polling interval hook
    lib/
      api.ts                    # Typed fetch wrappers
      utils.ts                  # Formatters, cn()
      glossary.ts               # Metric definitions + scoring weights
```

## License

MIT
