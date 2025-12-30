# coding=utf-8
"""
扩展数据源渲染模块

提供扩展数据源（加密货币、股票、Twitter）的格式化功能
"""

from typing import Dict, Optional, List


def render_extended_data_section(
    extended_data: Optional[Dict] = None,
    format_type: str = "wework",
) -> str:
    """
    渲染扩展数据源部分

    Args:
        extended_data: 扩展数据字典 {
            'crypto': {symbol: {price, change_24h, ...}},
            'stock': {symbol: {price, change_pct, market, name, ...}},
            'twitter': {author: [{content, ...}, ...]}
        }
        format_type: 格式类型 (wework, feishu, dingtalk, telegram, bark, slack, ntfy)

    Returns:
        格式化的扩展数据内容
    """
    if not extended_data:
        return ""

    # 检查是否有任何数据
    has_crypto = extended_data.get('crypto') and any(v for v in extended_data['crypto'].values())
    has_stock = extended_data.get('stock') and any(v for v in extended_data['stock'].values())
    has_twitter = extended_data.get('twitter') and any(v for v in extended_data['twitter'].values())

    if not (has_crypto or has_stock or has_twitter):
        return ""

    content = ""

    # 选择合适的格式化符号
    if format_type in ("wework", "bark", "ntfy", "dingtalk", "feishu"):
        # Markdown 格式
        section_title = "📊 **市场数据**\n\n"
        bold_start = "**"
        bold_end = "**"
        separator = "---"
    elif format_type == "telegram":
        # HTML 格式
        section_title = "📊 <b>市场数据</b>\n\n"
        bold_start = "<b>"
        bold_end = "</b>"
        separator = "━━━━━━━━━━━"
    elif format_type == "slack":
        # Slack mrkdwn 格式
        section_title = "📊 *市场数据*\n\n"
        bold_start = "*"
        bold_end = "*"
        separator = "---"
    else:
        # 默认 Markdown
        section_title = "📊 **市场数据**\n\n"
        bold_start = "**"
        bold_end = "**"
        separator = "---"

    content += section_title

    # 1. 加密货币部分
    if has_crypto:
        crypto_content = _render_crypto_data(extended_data['crypto'], bold_start, bold_end)
        if crypto_content:
            content += crypto_content + "\n"

    # 2. 股票部分
    if has_stock:
        stock_content = _render_stock_data(extended_data['stock'], bold_start, bold_end)
        if stock_content:
            content += stock_content + "\n"

    # 3. Twitter 部分
    if has_twitter:
        twitter_content = _render_twitter_data(extended_data['twitter'], bold_start, bold_end)
        if twitter_content:
            content += twitter_content + "\n"

    content += f"{separator}\n\n"

    return content


def _render_crypto_data(crypto_data: Dict, bold_start: str, bold_end: str) -> str:
    """渲染加密货币数据"""
    if not crypto_data:
        return ""

    content = f"💰 {bold_start}加密货币：{bold_end}\n"

    # 按价格变化排序（涨幅最大的在前）
    sorted_cryptos = sorted(
        [(symbol, data) for symbol, data in crypto_data.items() if data],
        key=lambda x: x[1].get('change_24h', 0),
        reverse=True
    )

    for symbol, data in sorted_cryptos[:5]:  # 最多显示5个
        # 去掉 USDT 后缀
        display_symbol = symbol.replace('USDT', '')

        price = data.get('price', 0)
        change = data.get('change_24h', 0)

        # 选择表情符号
        if change >= 5:
            emoji = "🔥"
        elif change > 0:
            emoji = "📈"
        elif change < -5:
            emoji = "💥"
        elif change < 0:
            emoji = "📉"
        else:
            emoji = "➖"

        # 格式化价格
        if price >= 1000:
            price_str = f"${price:,.0f}"
        elif price >= 1:
            price_str = f"${price:.2f}"
        else:
            price_str = f"${price:.4f}"

        # 格式化涨跌幅
        if change > 0:
            change_str = f"+{change:.2f}%"
        else:
            change_str = f"{change:.2f}%"

        content += f"• {emoji} {display_symbol}: {price_str} ({change_str})\n"

    return content


def _render_stock_data(stock_data: Dict, bold_start: str, bold_end: str) -> str:
    """渲染股票数据"""
    if not stock_data:
        return ""

    content = f"📈 {bold_start}重点股票：{bold_end}\n"

    # 按涨跌幅排序（涨幅最大的在前）
    sorted_stocks = sorted(
        [(symbol, data) for symbol, data in stock_data.items() if data],
        key=lambda x: x[1].get('change_pct', 0),
        reverse=True
    )

    for symbol, data in sorted_stocks[:5]:  # 最多显示5个
        name = data.get('name', symbol)
        market = data.get('market', '')
        price = data.get('price', 0)
        change = data.get('change_pct', 0)

        # 选择表情符号
        if change >= 5:
            emoji = "🔥"
        elif change > 0:
            emoji = "📈"
        elif change < -5:
            emoji = "💥"
        elif change < 0:
            emoji = "📉"
        else:
            emoji = "➖"

        # 格式化价格
        price_str = f"${price:.2f}" if market == "US" else f"{price:.2f}"

        # 格式化涨跌幅
        if change > 0:
            change_str = f"+{change:.2f}%"
        else:
            change_str = f"{change:.2f}%"

        # 构建显示名称
        if market:
            display_name = f"{name} ({market})"
        else:
            display_name = name

        content += f"• {emoji} {display_name}: {price_str} ({change_str})\n"

    return content


def _render_twitter_data(twitter_data: Dict, bold_start: str, bold_end: str) -> str:
    """渲染 Twitter 数据"""
    if not twitter_data:
        return ""

    content = f"🐦 {bold_start}Twitter 动态：{bold_end}\n"

    for author, tweets in twitter_data.items():
        if not tweets:
            continue

        # 只显示最新的推文
        latest_tweet = tweets[0] if isinstance(tweets, list) else tweets

        # 截取推文内容（最多100字符）
        tweet_content = latest_tweet.get('content', '')
        if len(tweet_content) > 100:
            tweet_content = tweet_content[:97] + "..."

        # 清理内容中的换行符
        tweet_content = tweet_content.replace('\n', ' ').strip()

        content += f"• @{author}: {tweet_content}\n"

    return content


def get_latest_extended_data_from_storage(storage_manager, date: Optional[str] = None) -> Optional[Dict]:
    """
    从存储后端获取最新的扩展数据

    Args:
        storage_manager: 存储管理器实例
        date: 日期字符串（可选）

    Returns:
        扩展数据字典或 None
    """
    try:
        import sqlite3
        from datetime import datetime

        # 获取后端实例
        backend = storage_manager.get_backend()

        # 只支持本地存储后端
        if not hasattr(backend, '_get_db_path'):
            return None

        # 获取数据库连接
        db_path = backend._get_db_path(date)
        if not db_path.exists():
            return None

        conn = backend._get_connection(date)
        cursor = conn.cursor()

        extended_data = {
            'crypto': {},
            'stock': {},
            'twitter': {}
        }

        # 获取最新的加密货币数据
        cursor.execute("""
            SELECT symbol, price_usd, price_change_24h, volume_24h, crawl_time
            FROM crypto_prices
            WHERE crawl_date = (SELECT MAX(crawl_date) FROM crypto_prices)
              AND crawl_time = (SELECT MAX(crawl_time) FROM crypto_prices WHERE crawl_date = (SELECT MAX(crawl_date) FROM crypto_prices))
            ORDER BY symbol
        """)
        for row in cursor.fetchall():
            symbol, price, change, volume, crawl_time = row
            extended_data['crypto'][symbol] = {
                'price': price,
                'change_24h': change,
                'volume_24h': volume,
            }

        # 获取最新的股票数据
        cursor.execute("""
            SELECT symbol, market, price, change_pct, volume, crawl_time
            FROM stock_prices
            WHERE crawl_date = (SELECT MAX(crawl_date) FROM stock_prices)
              AND crawl_time = (SELECT MAX(crawl_time) FROM stock_prices WHERE crawl_date = (SELECT MAX(crawl_date) FROM stock_prices))
            ORDER BY symbol
        """)
        for row in cursor.fetchall():
            symbol, market, price, change, volume, crawl_time = row
            # 尝试从 config 获取名称，如果没有则使用 symbol
            name = symbol  # 可以后续从配置中获取
            extended_data['stock'][symbol] = {
                'market': market,
                'name': name,
                'price': price,
                'change_pct': change,
                'volume': volume,
            }

        # 获取最新的 Twitter 数据（每个作者最新3条）
        cursor.execute("""
            SELECT author, content, post_url, published_time
            FROM (
                SELECT author, content, post_url, published_time,
                       ROW_NUMBER() OVER (PARTITION BY author ORDER BY crawl_time DESC) as rn
                FROM twitter_posts
                WHERE crawl_date = (SELECT MAX(crawl_date) FROM twitter_posts)
            ) t
            WHERE rn <= 3
            ORDER BY author, published_time DESC
        """)

        for row in cursor.fetchall():
            author, content, post_url, published_time = row
            if author not in extended_data['twitter']:
                extended_data['twitter'][author] = []
            extended_data['twitter'][author].append({
                'content': content,
                'post_url': post_url,
                'published_time': published_time,
            })

        return extended_data

    except Exception as e:
        print(f"获取扩展数据失败: {e}")
        return None
