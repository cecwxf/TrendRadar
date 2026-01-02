# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TrendRadar is a Python-based news trend monitoring and analysis platform that:
- Aggregates hot topics from 11+ Chinese news platforms (Toutiao, Baidu, Weibo, etc.)
- Matches news against configurable keyword lists (`config/frequency_words.txt`)
- Generates HTML reports with weighting/ranking algorithms
- Delivers notifications through 8+ channels (Feishu, DingTalk, Telegram, Email, Slack, etc.)
- Optionally integrates Claude AI for market insights
- Provides MCP server for interactive analysis via Claude Desktop

## Common Commands

### Development & Testing
```bash
# Run the crawler once (main entry point)
python3 -m trendradar

# Run with specific configuration
python3 -m trendradar --config config/config.yaml

# Test specific components
python3 test_integration.py          # Full pipeline integration
python3 test_ai_analysis.py          # Claude AI integration
python3 test_extended_sources.py     # Crypto/stock/Twitter fetchers
python3 test_notification_extended.py # Multi-channel notifications
python3 test_html_extended.py        # HTML report generation
```

### Deployment Scripts
```bash
# Local one-time execution
./run_crawler.sh

# Start web server to view HTML reports
./start_webserver.sh  # Serves on http://localhost:8080

# Real-time monitoring (10-second interval)
./start_realtime.sh   # Background daemon
./stop_realtime.sh    # Stop monitoring
tail -f /tmp/trendradar_realtime.log  # View logs

# Test notification channels
./test_feishu.sh      # Test Feishu webhook
```

### Docker Deployment
```bash
# Build and run
cd docker
docker-compose up -d

# Management
docker logs -f trend-radar
docker exec -it trend-radar python -m trendradar
docker-compose restart
docker-compose down
```

### MCP Server (Claude Desktop Integration)
```bash
# Start MCP server (configured in Claude Desktop)
python3 -m mcp_server.server

# Or via entry point
trendradar-mcp
```

## Architecture

### Core Application Flow
Entry point: `trendradar/__main__.py` → `NewsAnalyzer` class

**Execution Pipeline:**
1. Load configuration (`config/config.yaml`)
2. Detect environment (GitHub Actions/Docker/local)
3. Fetch news from NewsNow API (`trendradar/crawler/fetcher.py`)
4. Optionally fetch extended data (crypto/stocks/Twitter via specialized fetchers)
5. Save to storage backend (SQLite + optional S3-compatible cloud storage)
6. Analyze news against frequency words with weighting algorithm
7. Optionally generate AI analysis via Claude API (`trendradar/ai/claude_analyzer.py`)
8. Generate HTML reports (`trendradar/report/generator.py`)
9. Dispatch notifications to configured channels (`trendradar/notification/dispatcher.py`)
10. Cleanup old data based on retention policy

### Report Modes (Critical Configuration)
Configured in `config/config.yaml` → `crawler.report_mode`:

- **`incremental`**: Only push newly appeared news items (prevents duplicates)
- **`current`**: Push current leaderboard + new items (real-time hot topics)
- **`daily`**: Push comprehensive summary + new items (full daily digest)

### Storage Architecture
`trendradar/storage/manager.py` auto-selects backend:

- **Local**: SQLite database + TXT/HTML snapshots in `output/` directory
- **Remote**: S3-compatible cloud storage (R2, OSS, COS, AWS S3) for GitHub Actions
- **Auto**: Detects environment and chooses appropriate backend

### Key Modules

**Crawler** (`trendradar/crawler/`):
- `fetcher.py`: NewsNow API client with retry logic and proxy support
- `crypto_fetcher.py`, `crypto_fetcher_coingecko.py`: Cryptocurrency price data
- `stock_fetcher.py`: Yahoo Finance integration for stocks
- `twitter_fetcher.py`: Twitter API v2 integration

**Notification** (`trendradar/notification/`):
- `dispatcher.py`: Multi-channel notification orchestrator
- `renderer.py`: Platform-specific message formatting (Markdown/plain text)
- Supports multiple accounts per channel (semicolon-separated URLs)

**AI Analysis** (`trendradar/ai/`):
- `claude_analyzer.py`: Anthropic API integration for market trend analysis
- Combines news, crypto, stock, and Twitter data into comprehensive insights
- Configurable model (default: `claude-3-5-sonnet-20241022`)

**MCP Server** (`mcp_server/`):
- FastMCP 2.0 server providing tools for Claude Desktop
- `tools/data_query.py`: Query news by date range, source, keywords
- `tools/analytics.py`: Sentiment analysis, trend comparison
- `tools/search_tools.py`: Full-text search with advanced filtering
- `utils/date_parser.py`: Natural language date resolution ("本周", "最近7天")

### Configuration System

**Main Config**: `config/config.yaml`
- App settings (version checking, timezone)
- Storage backend selection and S3 credentials
- Crawler settings (request intervals, proxy, platform list)
- Report modes and rank thresholds
- Notification channels (webhooks, batch sizes, time windows)
- Extended data sources (crypto, stocks, Twitter)
- AI analysis (Claude API key, model selection)

**Frequency Words**: `config/frequency_words.txt`
Syntax:
- Word groups separated by blank lines
- Normal words: Match any occurrence
- `+prefix`: Required words (all must match)
- `!prefix`: Filter words (exclude matches)
- `@number`: Max display limit per group
- `[GLOBAL_FILTER]`: Universal exclusions

**Environment Variables** (`.env` or GitHub Secrets):
- `FEISHU_WEBHOOK_URL`, `DINGTALK_WEBHOOK_URL`: Notification webhooks
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`: Telegram config
- `HTTP_PROXY`, `HTTPS_PROXY`: Network proxy
- `CLAUDE_API_KEY`: Anthropic API key
- `S3_ENDPOINT_URL`, `S3_BUCKET_NAME`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`: Remote storage

### Dependency Injection Pattern
`trendradar/context.py` provides `AppContext` class that encapsulates:
- Configuration access
- Time zone handling
- Storage management
- Report generation
- Notification rendering

**Important**: All configuration-dependent code uses `AppContext` instead of global imports. Always pass `AppContext` instance through function parameters.

## Development Notes

### When modifying notification channels:
- Update `trendradar/notification/dispatcher.py` to add new channel
- Add corresponding formatter in `formatters.py`
- Update `config/config.yaml` schema
- Add environment variable to `.env.example`
- Multi-account support requires semicolon-separated validation

### When adding new data sources:
- Create fetcher in `trendradar/crawler/` (extend base pattern)
- Update storage schema in `trendradar/storage/base.py`
- Add rendering logic in `trendradar/report/extended_renderer.py`
- Update configuration in `config/config.yaml`

### When modifying report generation:
- Main logic in `trendradar/report/generator.py`
- HTML templates in `trendradar/report/html.py`
- Weighting algorithm in `trendradar/core/analyzer.py`
- Format helpers in `trendradar/report/formatter.py`

### When adding MCP tools:
- Create tool module in `mcp_server/tools/`
- Register in `mcp_server/server.py`
- Use `DateParser` from `utils/date_parser.py` for date handling
- Update `README-MCP-FAQ.md` with usage examples

### Testing notification channels:
Always test webhooks before deployment:
```bash
# Test Feishu
curl -X POST "$FEISHU_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{"msg_type":"text","content":{"text":"测试消息"}}'

# Expected response: {"code":0}
```

### Proxy configuration:
The crawler supports HTTP proxy for accessing restricted APIs (CoinGecko, Twitter):
- Set `HTTP_PROXY` and `HTTPS_PROXY` in `.env`
- Configure in `run_crawler.sh` or `docker/.env`
- Proxy applies to all data fetchers

### Data retention:
SQLite database and reports are automatically cleaned based on retention policy in `config/config.yaml` → `storage.retention_days`

## Important Implementation Details

### Weighting System
News items are weighted by:
- **Rank**: Higher platform rank = higher weight
- **Frequency**: Multiple appearances increase weight
- **Time decay**: Recent news weighted higher

Configurable parameters in `config/config.yaml` → `crawler.ranking_config`

### Push Time Windows
Notifications can be restricted to specific hours:
```yaml
notification:
  push_window:
    enabled: true
    start_time: "08:00"
    end_time: "22:00"
    once_per_day: false
```

### Remote Storage Sync
For GitHub Actions deployment:
- On each run, pull latest data from S3
- After processing, push updated database to S3
- MCP server can pull remote data for local analysis

### Security Considerations
- Never commit `.env` file (use `.env.example` template)
- Webhook URLs and API keys via environment variables only
- Validate all user inputs in MCP server tools
- Sanitize URLs before rendering in HTML reports
