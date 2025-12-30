-- TrendRadar 数据库表结构

-- ============================================
-- 平台信息表
-- 核心：id 不变，name 可变
-- ============================================
CREATE TABLE IF NOT EXISTS platforms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 新闻条目表
-- 以 URL + platform_id 为唯一标识，支持去重存储
-- ============================================
CREATE TABLE IF NOT EXISTS news_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    platform_id TEXT NOT NULL,
    rank INTEGER NOT NULL,
    url TEXT DEFAULT '',
    mobile_url TEXT DEFAULT '',
    first_crawl_time TEXT NOT NULL,      -- 首次抓取时间
    last_crawl_time TEXT NOT NULL,       -- 最后抓取时间
    crawl_count INTEGER DEFAULT 1,       -- 抓取次数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (platform_id) REFERENCES platforms(id)
);

-- ============================================
-- 标题变更历史表
-- 记录同一 URL 下标题的变化
-- ============================================
CREATE TABLE IF NOT EXISTS title_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_item_id INTEGER NOT NULL,
    old_title TEXT NOT NULL,
    new_title TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (news_item_id) REFERENCES news_items(id)
);

-- ============================================
-- 排名历史表
-- 记录每次抓取时的排名变化
-- ============================================
CREATE TABLE IF NOT EXISTS rank_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_item_id INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    crawl_time TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (news_item_id) REFERENCES news_items(id)
);

-- ============================================
-- 抓取记录表
-- 记录每次抓取的时间和数量
-- ============================================
CREATE TABLE IF NOT EXISTS crawl_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_time TEXT NOT NULL UNIQUE,
    total_items INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 抓取来源状态表
-- 记录每次抓取各平台的成功/失败状态
-- ============================================
CREATE TABLE IF NOT EXISTS crawl_source_status (
    crawl_record_id INTEGER NOT NULL,
    platform_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('success', 'failed')),
    PRIMARY KEY (crawl_record_id, platform_id),
    FOREIGN KEY (crawl_record_id) REFERENCES crawl_records(id),
    FOREIGN KEY (platform_id) REFERENCES platforms(id)
);

-- ============================================
-- 推送记录表
-- 用于 push_window once_per_day 功能
-- ============================================
CREATE TABLE IF NOT EXISTS push_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    pushed INTEGER DEFAULT 0,
    push_time TEXT,
    report_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 索引定义
-- ============================================

-- 平台索引
CREATE INDEX IF NOT EXISTS idx_news_platform ON news_items(platform_id);

-- 时间索引（用于查询最新数据）
CREATE INDEX IF NOT EXISTS idx_news_crawl_time ON news_items(last_crawl_time);

-- 标题索引（用于标题搜索）
CREATE INDEX IF NOT EXISTS idx_news_title ON news_items(title);

-- URL + platform_id 唯一索引（仅对非空 URL，实现去重）
CREATE UNIQUE INDEX IF NOT EXISTS idx_news_url_platform
    ON news_items(url, platform_id) WHERE url != '';

-- 抓取状态索引
CREATE INDEX IF NOT EXISTS idx_crawl_status_record ON crawl_source_status(crawl_record_id);

-- 排名历史索引
CREATE INDEX IF NOT EXISTS idx_rank_history_news ON rank_history(news_item_id);

-- ============================================
-- 扩展数据源表（加密货币、股票、Twitter、AI 分析）
-- ============================================

-- ============================================
-- 加密货币价格表
-- 存储 BTC/ETH 等加密货币的实时价格数据
-- ============================================
CREATE TABLE IF NOT EXISTS crypto_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,              -- 交易对符号 (如 BTCUSDT, ETHUSDT)
    price_usd REAL NOT NULL,           -- 美元价格
    price_change_24h REAL,             -- 24小时涨跌幅（百分比）
    volume_24h REAL,                   -- 24小时交易量
    high_24h REAL,                     -- 24小时最高价
    low_24h REAL,                      -- 24小时最低价
    market_cap REAL,                   -- 市值（可选）
    crawl_time TEXT NOT NULL,          -- 抓取时间 (HH:MM)
    crawl_date TEXT NOT NULL,          -- 抓取日期 (YYYY-MM-DD)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, crawl_time, crawl_date)
);

-- ============================================
-- 股票价格表
-- 存储美股/港股/A股的实时价格数据
-- ============================================
CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,              -- 股票代码 (如 AAPL, 0700.HK, 600519.SS)
    market TEXT NOT NULL,              -- 市场 (US, HK, CN)
    price REAL NOT NULL,               -- 当前价格
    change_pct REAL,                   -- 涨跌幅百分比
    volume REAL,                       -- 成交量
    open_price REAL,                   -- 开盘价
    high_price REAL,                   -- 最高价
    low_price REAL,                    -- 最低价
    crawl_time TEXT NOT NULL,          -- 抓取时间
    crawl_date TEXT NOT NULL,          -- 抓取日期
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, market, crawl_time, crawl_date)
);

-- ============================================
-- Twitter 推文表
-- 存储特定用户的 Twitter 推文
-- ============================================
CREATE TABLE IF NOT EXISTS twitter_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author TEXT NOT NULL,              -- 作者用户名 (如 SiliconWang)
    content TEXT NOT NULL,             -- 推文内容
    post_url TEXT NOT NULL,            -- 推文链接
    published_time TEXT,               -- 发布时间
    crawl_time TEXT NOT NULL,          -- 抓取时间
    crawl_date TEXT NOT NULL,          -- 抓取日期
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_url)
);

-- ============================================
-- AI 分析结果表
-- 存储 Claude/ChatGPT 的综合分析结果
-- ============================================
CREATE TABLE IF NOT EXISTS ai_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_type TEXT NOT NULL,       -- 分析类型 (news, crypto, stock, comprehensive)
    content TEXT NOT NULL,             -- 分析内容
    data_snapshot TEXT,                -- 数据快照 (JSON 格式，可选)
    model TEXT DEFAULT 'claude-3-5-sonnet',  -- AI 模型
    tokens_used INTEGER,               -- Token 使用量
    crawl_time TEXT NOT NULL,          -- 分析时间
    crawl_date TEXT NOT NULL,          -- 分析日期
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 扩展数据源索引
-- ============================================

-- 加密货币索引
CREATE INDEX IF NOT EXISTS idx_crypto_symbol_time ON crypto_prices(symbol, crawl_date, crawl_time);
CREATE INDEX IF NOT EXISTS idx_crypto_date ON crypto_prices(crawl_date);

-- 股票索引
CREATE INDEX IF NOT EXISTS idx_stock_symbol_time ON stock_prices(symbol, crawl_date, crawl_time);
CREATE INDEX IF NOT EXISTS idx_stock_market ON stock_prices(market);
CREATE INDEX IF NOT EXISTS idx_stock_date ON stock_prices(crawl_date);

-- Twitter 索引
CREATE INDEX IF NOT EXISTS idx_twitter_author_time ON twitter_posts(author, crawl_date, crawl_time);
CREATE INDEX IF NOT EXISTS idx_twitter_date ON twitter_posts(crawl_date);

-- AI 分析索引
CREATE INDEX IF NOT EXISTS idx_ai_analysis_time ON ai_analysis(crawl_date, crawl_time);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_type ON ai_analysis(analysis_type);
